import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from epg import app
from epg.database import storage_models as sm

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
    assert response.json()["detail"] == "Email already registered"

    await delete_user(db, DUPLICATE_EMAIL)
