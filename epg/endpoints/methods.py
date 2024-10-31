from http.client import HTTPException
from typing import Optional

from epg.database import storage_models as sm
from epg.dependencies import database
from epg.utils import calculate_distance
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import EmailStr
from sqlalchemy import asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

app = APIRouter()


@app.get("")
async def get_user_list(
        email: EmailStr = Query(description="Почта текущего пользователя"),
        gender: Optional[str] = Query(None, description="Фильтр по полу"),
        first_name: Optional[str] = Query(None, description="Фильтр по имени"),
        last_name: Optional[str] = Query(None, description="Фильтр по фамилии"),
        sort_by_registration_date: Optional[str] = Query(None,
                                                         description="Сортировать по дате регистрации (asc или desc)"),
        distance: Optional[float] = Query(None, description="Расстояние в км"),
        db: AsyncSession = Depends(database)
):
    try:
        current_user = (await db.execute(select(sm.User).where(sm.User.email == email))).scalar_one_or_none()
        if not current_user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        query = select(sm.User)

        if gender:
            query = query.where(sm.User.gender == gender)
        if first_name:
            query = query.where(sm.User.first_name.ilike(f"%{first_name}%"))
        if last_name:
            query = query.where(sm.User.last_name.ilike(f"%{last_name}%"))
        if sort_by_registration_date:
            if sort_by_registration_date.lower() == 'asc':
                query = query.order_by(asc(sm.User.date))
            elif sort_by_registration_date.lower() == 'desc':
                query = query.order_by(desc(sm.User.date))
        result = await db.execute(query)
        users = result.scalars().all()
        if distance:
            users_within_distance = [user for user in users if
                                     user.latitude and
                                     user.longitude and
                                     await calculate_distance(current_user.latitude, current_user.longitude,
                                                              user.latitude,
                                                              user.longitude) < distance
                                     and user.email != current_user.email]
            return {"users": users_within_distance}
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Unexpected error " + str(e))
