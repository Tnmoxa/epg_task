import os

import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()


@pytest_asyncio.fixture()
async def db():
    return create_async_engine(os.environ.get('DATABASE_URL'))
