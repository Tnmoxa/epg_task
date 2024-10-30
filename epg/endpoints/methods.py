from http.client import HTTPException
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query
from sqlalchemy import asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from epg.database import storage_models as sm
from epg.dependencies import database

app = APIRouter()


@app.get("")
async def get_user_list(
        gender: Optional[str] = Query(None, description="Фильтр по полу"),
        first_name: Optional[str] = Query(None, description="Фильтр по имени"),
        last_name: Optional[str] = Query(None, description="Фильтр по фамилии"),
        sort_by_registration_date: Optional[str] = Query(None,
                                                         description="Сортировать по дате регистрации (asc or desc)"),
        db: AsyncSession = Depends(database)
):
    try:
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

        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Unexpected error " + str(e))
