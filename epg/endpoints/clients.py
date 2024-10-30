import datetime
import hashlib
import os.path
from io import BytesIO

from PIL import Image
from fastapi import APIRouter, Depends, HTTPException
from fastapi import UploadFile, Form
from fastapi.concurrency import run_in_threadpool
from fastapi.security import OAuth2PasswordBearer
from pydantic import EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from epg.database import api_models as am
from epg.database import storage_models as sm
from epg.dependencies import database, email_sender

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="clients/token")
app = APIRouter()

resource_path = os.path.join(os.path.dirname(__file__), '../../resources')
watermark_path = os.path.join(resource_path, 'watermark.png')
images_path = os.path.join(resource_path, 'images')
os.makedirs(images_path, exist_ok=True)
RATING_LIMIT_PER_DAY = int(os.environ.get('RATING_LIMIT_PER_DAY'))


def add_watermark(avatar_data: bytes) -> str:
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
                 gender: str = Form(...),
                 first_name: str = Form(...),
                 last_name: str = Form(...),
                 email: EmailStr = Form(...),
                 password: str = Form(...),
                 db: AsyncSession = Depends(database)):
    try:
        avatar_bytes = await avatar.read()

        hash_part = await run_in_threadpool(add_watermark, avatar_bytes)

        user = am.AuthUser(email=email, password=password)

        user_instance = sm.User(
            gender=gender,
            avatar=os.path.join(images_path, f'{hash_part}.png'),
            first_name=first_name,
            last_name=last_name,
            email=user.email,
            password=user.password
        )
        db.add(user_instance)
        await db.commit()
        return "Ok"
    except IntegrityError:
        raise HTTPException(status_code=422, detail="Электронная почта уже используется")


@app.post("/{id}/match")
async def match(
        id: int,
        email: EmailStr = Form(...),
        db: AsyncSession = Depends(database)
):
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
