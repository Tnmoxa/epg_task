import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from epg.database import storage_models as sm
from epg.endpoints import app

client = TestClient(app)

TEST_EMAIL = "test@example.com"
DUPLICATE_EMAIL = "duplicate@example.com"
TEST_PASSWORD = "TestPassword123"
avatar_path = os.path.join(os.path.dirname(__file__), 'test.png')


async def register_user(email: str):
    avatar_file = Path(avatar_path)
    with avatar_file.open("rb") as avatar_data:
        response = client.post(
            "/api/clients/create",
            files={"avatar": (avatar_file.name, avatar_data, "image/png")},
            data={
                "username": "testuser",
                "gender": "male",
                "first_name": "John",
                "last_name": "Doe",
                "email": email,
                "password": TEST_PASSWORD,
            },
        )
    return response


async def delete_user(db, email: str):
    async with AsyncSession(db) as session:
        result = await session.execute(select(sm.User).where(sm.User.email == email))
        user = result.scalar_one_or_none()

        if user:
            await session.delete(user)
            await session.commit()


async def delete_match(db, rater_id: int, rated_id: int):
    async with AsyncSession(db) as session:
        result = await session.execute(
            select(sm.Rating).where(sm.Rating.rater_id == rater_id, sm.Rating.rated_id == rated_id))
        user = result.scalar_one_or_none()

        if user:
            await session.delete(user)
            await session.commit()


async def get_user(db, email):
    async with AsyncSession(db) as session:
        return (await session.execute(select(sm.User).where(sm.User.email == email))).scalar_one_or_none()


@pytest.mark.asyncio
async def test_user_creation(db):
    response = await register_user(TEST_EMAIL)
    assert response.status_code == 200

    await delete_user(db, TEST_EMAIL)


@pytest.mark.asyncio
async def test_duplicate_email(db):
    await register_user(DUPLICATE_EMAIL)
    response = await register_user(DUPLICATE_EMAIL)
    assert response.status_code == 422
    assert response.json()["detail"] == "Электронная почта уже используется"

    await delete_user(db, DUPLICATE_EMAIL)


@pytest.mark.asyncio
async def test_match_success(db):
    await register_user(TEST_EMAIL)
    await register_user(DUPLICATE_EMAIL)
    test_email_id = await get_user(db, TEST_EMAIL)
    duplicate_email_id = await get_user(db, DUPLICATE_EMAIL)

    # Выполняем оценку
    response = client.post(f"/api/clients/{test_email_id.id}/match", data={"email": TEST_EMAIL})
    assert response.status_code == 400
    assert response.json()["detail"] == "Вы не можете оценить себя"

    response = client.post(f"/api/clients/{duplicate_email_id.id}/match", data={"email": TEST_EMAIL})

    assert response.status_code == 200
    assert response.json()["message"] == "Оценка добавлена"

    response = client.post(f"/api/clients/{duplicate_email_id.id}/match", data={"email": TEST_EMAIL})

    assert response.status_code == 400
    assert response.json()["detail"] == "Вы уже оценили этого участника"

    await delete_match(db, test_email_id.id, duplicate_email_id.id)
    await delete_user(db, TEST_EMAIL)
    await delete_user(db, DUPLICATE_EMAIL)


@pytest.mark.asyncio
async def test_match_rating_limit(db):
    RATING_LIMIT_PER_DAY = 5
    await register_user(TEST_EMAIL)
    for i in range(RATING_LIMIT_PER_DAY):
        await register_user(f'{i}' + TEST_EMAIL)
        response = client.post(f"/api/clients/{(await get_user(db, f'{i}' + TEST_EMAIL)).id}/match",
                               data={"email": TEST_EMAIL})
        assert response.status_code == 200

    await register_user(f'{RATING_LIMIT_PER_DAY}' + TEST_EMAIL)
    response = client.post(f"/api/clients/{(await get_user(db, '5' + TEST_EMAIL)).id}/match",
                           data={"email": TEST_EMAIL})

    assert response.status_code == 429
    assert response.json()["detail"] == "Лимит оценок в день превышен"

    for i in range(RATING_LIMIT_PER_DAY + 1):
        await delete_match(db, (await get_user(db, TEST_EMAIL)).id, (await get_user(db, f'{i}' + TEST_EMAIL)).id)
        await delete_user(db, f'{i}' + TEST_EMAIL)

    await delete_user(db, TEST_EMAIL)
