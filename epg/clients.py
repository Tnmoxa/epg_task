from sqlalchemy.exc import IntegrityError
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from epg.database import api_models as am
from epg.database import storage_models as sm
from epg.dependencies import database

app = FastAPI()


@app.get("/")
async def session():
    return "Hello World!"


@app.post("/create")
async def create(user: am.User, db: AsyncSession = Depends(database)):
    try:
        user_instance = sm.User(
            gender=user.gender,
            avatar='aweqwe',
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            password=user.password
        )
        db.add(user_instance)
        await db.commit()
        return "Ok"
    except IntegrityError:
        raise HTTPException(status_code=422, detail="Email already registered")
