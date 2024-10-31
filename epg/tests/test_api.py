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
                "gender": "male",
                "first_name": "John",
                "last_name": "Doe",
                "email": email,
                "password": TEST_PASSWORD,
                "latitude": 0,
                "longitude": 0,
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

    response = client.post(f"/api/clients/{test_email_id.id}/match", params={"email": TEST_EMAIL})
    assert response.status_code == 400
    assert response.json()["detail"] == "Вы не можете оценить себя"

    response = client.post(f"/api/clients/{duplicate_email_id.id}/match", params={"email": TEST_EMAIL})

    assert response.status_code == 200
    assert response.json()["message"] == "Оценка добавлена"

    response = client.post(f"/api/clients/{duplicate_email_id.id}/match", params={"email": TEST_EMAIL})

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
                               params={"email": TEST_EMAIL})
        assert response.status_code == 200

    await register_user(f'{RATING_LIMIT_PER_DAY}' + TEST_EMAIL)
    response = client.post(f"/api/clients/{(await get_user(db, '5' + TEST_EMAIL)).id}/match",
                           params={"email": TEST_EMAIL})

    assert response.status_code == 429
    assert response.json()["detail"] == "Лимит оценок в день превышен"

    for i in range(RATING_LIMIT_PER_DAY + 1):
        await delete_match(db, (await get_user(db, TEST_EMAIL)).id, (await get_user(db, f'{i}' + TEST_EMAIL)).id)
        await delete_user(db, f'{i}' + TEST_EMAIL)

    await delete_user(db, TEST_EMAIL)


async def advanced_register_user(gender: str, first_name: str, last_name: str, email: str):
    avatar_file = Path(avatar_path)
    with avatar_file.open("rb") as avatar_data:
        response = client.post(
            "/api/clients/create",
            files={"avatar": (avatar_file.name, avatar_data, "image/png")},
            data={
                "gender": gender,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "password": TEST_PASSWORD,
                "latitude": 0,
                "longitude": 0,
            },
        )
    return response


@pytest.mark.asyncio
async def test_get_user_list(db):
    await advanced_register_user("female", "first_name0", "last_name0", TEST_EMAIL)

    await advanced_register_user("male", "first_name1", "last_name2", "test_username1@example.com")
    await advanced_register_user("male", "first_name2", "last_name2", "test_username2@example.com")
    await advanced_register_user("female", "first_name1", "last_name1", "test_username3@example.com")
    await advanced_register_user("female", "first_name2", "last_name1", "test_username4@example.com")

    response = client.get("/api/list", params={"first_name": "first_name1", "email": TEST_EMAIL})
    assert response.status_code == 200
    users = response.json()['users']
    assert all(user["first_name"] == "first_name1" for user in users)

    response = client.get("/api/list", params={"gender": "male", "email": TEST_EMAIL})
    assert response.status_code == 200
    users = response.json()['users']
    assert all(user["gender"] == "male" for user in users)

    response = client.get("/api/list", params={"last_name": "last_name2", "email": TEST_EMAIL})
    assert response.status_code == 200
    users = response.json()['users']
    assert all(user["last_name"] == "last_name2" for user in users)

    response = client.get("/api/list", params={"sort_by_registration_date": "asc", "email": TEST_EMAIL})
    assert response.status_code == 200
    users = response.json()['users']
    dates = [user["date"] for user in users]
    assert dates == sorted(dates)

    response = client.get("/api/list", params={"sort_by_registration_date": "desc", "email": TEST_EMAIL})
    assert response.status_code == 200
    users = response.json()['users']
    dates = [user["date"] for user in users]
    assert dates == sorted(dates, reverse=True)

    response = client.get("/api/list", params={"first_name": "first_name1", "last_name": "last_name2", "gender": "male",
                                               "email": TEST_EMAIL})
    assert response.status_code == 200
    users = response.json()['users']
    any(user["email"] == "test_username1@example.com" for user in users)

    await delete_user(db, TEST_EMAIL)
    await delete_user(db, "test_username1@example.com")
    await delete_user(db, "test_username2@example.com")
    await delete_user(db, "test_username3@example.com")
    await delete_user(db, "test_username4@example.com")


async def advanced_register_user_with_latlong(gender: str, first_name: str, last_name: str, email: str, latitude: float,
                                              longitude: float):
    avatar_file = Path(avatar_path)
    with avatar_file.open("rb") as avatar_data:
        response = client.post(
            "/api/clients/create",
            files={"avatar": (avatar_file.name, avatar_data, "image/png")},
            data={
                "gender": gender,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "password": TEST_PASSWORD,
                "latitude": latitude,
                "longitude": longitude,
            },
        )
    return response


@pytest.mark.asyncio
async def test_get_users_within_distance(db):
    current_user_email = "current_user@example.com"
    await advanced_register_user_with_latlong("male", "Current", "User", current_user_email, latitude=0.0,
                                              longitude=0.0)

    nearby_user_email = "nearby_user@example.com"
    distant_user_email = "distant_user@example.com"
    await advanced_register_user_with_latlong("female", "Nearby", "User", nearby_user_email, latitude=0.01,
                                              longitude=0.01)
    await advanced_register_user_with_latlong("female", "Distant", "User", distant_user_email, latitude=10.0,
                                              longitude=10.0)

    distance_km = 2.0

    response = client.get("/api/list", params={"email": current_user_email, "distance": distance_km})
    assert response.status_code == 200
    users_within_distance = response.json()['users']

    assert any(user["email"] == nearby_user_email for user in users_within_distance)
    assert not any(user["email"] == distant_user_email for user in users_within_distance)

    await delete_user(db, current_user_email)
    await delete_user(db, nearby_user_email)
    await delete_user(db, distant_user_email)
