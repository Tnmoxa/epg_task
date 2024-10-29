import os
from contextlib import asynccontextmanager

from alembic.config import Config
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

load_dotenv()


# Класс базы данных для работы с fastapi
class Database:
    def __init__(self, link):
        self.engine = create_async_engine(link)
        self._async_session = async_sessionmaker(self.engine, expire_on_commit=False)

    async def __call__(self):
        async with self._async_session() as session:
            yield session


database = Database(os.environ.get('DATABASE_URL'))

alembic_cfg = Config("./alembic.ini")


@asynccontextmanager
async def lifespan(_):
    # Инициализация БД
    # if not os.path.exists(os.environ.get('DATABASE_URL')):
    #     command.upgrade(alembic_cfg, "head")
    # print("Database upgraded to the latest revision.")

    yield
