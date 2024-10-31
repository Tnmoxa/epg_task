import datetime
import hashlib
import os.path
from io import BytesIO

from PIL import Image
from epg.database import api_models as am
from epg.database import storage_models as sm
from epg.dependencies import database, email_sender
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.security import OAuth2PasswordBearer
from pydantic import EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="clients/token")
app = APIRouter()

resource_path = os.path.join(os.path.dirname(__file__), '../../resources')
watermark_path = os.path.join(resource_path, 'watermark.png')
images_path = os.path.join(resource_path, 'images')
os.makedirs(images_path, exist_ok=True)
RATING_LIMIT_PER_DAY = int(os.environ.get('RATING_LIMIT_PER_DAY'))


def add_watermark(avatar_data: bytes) -> str:
    """
    Добавляет водяной знак к изображению аватара и сохраняет его.

    Args:
        avatar_data: Исходные данные изображения аватара в байтах.

    Returns:
        str: Хэш обработанного изображения, используемый в качестве уникального идентификатора.

    """

    image_data = BytesIO(avatar_data)

    image_hash = hashlib.md5(image_data.getvalue()).hexdigest()
    hash_part = image_hash[:8]

    with Image.open(watermark_path).convert("RGBA") as watermark:
        with Image.open(image_data).convert("RGBA") as base_image:
            base_width, base_height = base_image.size
            watermark_size = (base_width // 6, base_height // 6)
            watermark = watermark.resize(watermark_size, Image.LANCZOS)

            alpha = watermark.split()[3]
            alpha = alpha.point(lambda p: p * 0.5)
            watermark.putalpha(alpha)

            position = (base_width - watermark_size[0], base_height - watermark_size[1])
            base_image.paste(watermark, position, watermark)
            output = BytesIO()
            base_image.save(output, format="PNG")
            output.seek(0)
    with open(os.path.join(images_path, f'{hash_part}.png'), "wb") as out_file:
        out_file.write(output.getbuffer())
    return hash_part


@app.post("/create")
async def create(avatar: UploadFile,
                 user: am.User = Depends(am.User.as_form),
                 db: AsyncSession = Depends(database)):
    """
    Создает нового пользователя и добавляет запись в базу данных.

    Args:
        avatar (UploadFile): Изображение аватара, загруженное пользователем.
        user (am.User): Данные формы пользователя, содержащие имя, адрес электронной почты и т. д.
        db (AsyncSession): Сеанс базы данных.

    Returns:
        str: Сообщение об успешном создании аккаунта.

    Raises:
        HTTPException: Если адрес электронной почты уже используется.
    """

    try:
        avatar_bytes = await avatar.read()

        hash_part = await run_in_threadpool(add_watermark, avatar_bytes)

        user_instance = sm.User(
            gender=user.gender,
            avatar=os.path.join(images_path, f'{hash_part}.png'),
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            password=user.password,
            date=datetime.datetime.now(),
            latitude=user.latitude,
            longitude=user.longitude
        )
        db.add(user_instance)
        await db.commit()
        return "Ok"
    except IntegrityError:
        raise HTTPException(status_code=422, detail="Электронная почта уже используется")


@app.post("/{id}/match")
async def match(
        id: int,
        email: EmailStr = Query(description="Почта текущего пользователя"),
        db: AsyncSession = Depends(database)
):
    """
    Добавляет оценку текущего пользователя другому пользователю и проверяет наличие взаимного интереса.
    Отправляет уведомление по электронной почте в случае взаимного соответствия.

    Args:
        id (int): Идентификатор оцениваемого пользователя.
        email (EmailStr): Адрес электронной почты текущего пользователя.
        db (AsyncSession): Сеанс базы данных.

    Returns:
        dict: Сообщение, указывающее на успех или взаимный интерес.

    Raises: HTTPException: Если пользователь не найден, пользователь сам себя оценил, превысил дневной лимит или
    пользователь уже оценил.
    """

    try:
        current_user = (await db.execute(select(sm.User).where(sm.User.email == email))).scalar_one_or_none()
        receiver = (await db.execute(select(sm.User).where(sm.User.id == id))).scalar_one_or_none()

        if not current_user or not receiver:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        if current_user.id == id:
            raise HTTPException(status_code=400, detail="Вы не можете оценить себя")
        today = datetime.datetime.now().date()
        ratings_today = await db.execute(
            select(sm.Rating)
            .where(sm.Rating.rater_id == current_user.id,
                   sm.Rating.date >= today,
                   sm.Rating.date < today + datetime.timedelta(days=1)
                   )
        )
        ratings_count = len(ratings_today.scalars().all())

        if ratings_count >= RATING_LIMIT_PER_DAY:
            raise HTTPException(status_code=429, detail="Лимит оценок в день превышен")

        rate = sm.Rating(rater_id=current_user.id, rated_id=id, date=datetime.datetime.now())
        db.add(rate)
        await db.commit()

        mutual = (await db.execute(select(sm.Rating).where(
            sm.Rating.rater_id == id,
            sm.Rating.rated_id == current_user.id
        ))).scalar_one_or_none()

        if mutual:
            matched_user_query = await db.execute(select(sm.User).where(sm.User.id == id))
            matched_user = matched_user_query.scalar_one_or_none()
            if matched_user:
                await email_sender(
                    matched_user.email,
                    f"Вам понравился {current_user.first_name}! Почта участника: {current_user.email}"
                )
                await email_sender(
                    current_user.email,
                    f"Вам понравился {matched_user.first_name}! Почта участника: {matched_user.email}"
                )
            return {"message": "Взаимная симпатия! Проверьте почту"}
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Вы уже оценили этого участника")
    return {"message": "Оценка добавлена"}
