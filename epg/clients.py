import hashlib
import os.path
from io import BytesIO

from PIL import Image
from fastapi import FastAPI, Depends, HTTPException
from fastapi import UploadFile, Form
from fastapi.concurrency import run_in_threadpool
from pydantic import EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from epg.database import storage_models as sm
from epg.dependencies import database

app = FastAPI()

resource_path = os.path.join(os.path.dirname(__file__), '../resources')

watermark_path = os.path.join(resource_path, 'watermark.png')
images_path = os.path.join(resource_path, 'images')
os.makedirs(images_path, exist_ok=True)


# executor = ThreadPoolExecutor(max_workers=5)


@app.get("/")
async def session():
    return "Hello World!"


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

        # loop = asyncio.get_running_loop()
        # hash_part = await loop.run_in_executor(executor, add_watermark, avatar_bytes)

        user_instance = sm.User(
            gender=gender,
            avatar=os.path.join(images_path, f'{hash_part}.png'),
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password
        )
        db.add(user_instance)
        await db.commit()
        return "Ok"
    except IntegrityError:
        raise HTTPException(status_code=422, detail="Email already registered")
