import os
from contextlib import asynccontextmanager
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
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

# Класс отправщика сообщений на почту
class EmailSender:
    def __init__(self):
        self.sender = os.environ.get('SMTP_EMAIL_FROM')
        self.password = os.environ.get('SMTP_EMAIL_FROM_PASSWORD')
        self.smtp_server = 'smtp.mail.ru'
        self.port = 465

    async def __call__(self, recipient_email: str, message: str):
        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender
            msg["To"] = recipient_email
            msg["Subject"] = "Уведомление о взаимной симпатии"
            msg.attach(MIMEText(message, "plain"))
            async with aiosmtplib.SMTP(hostname="smtp.mail.ru", port=465, use_tls=True) as server:
                await server.login(self.sender, self.password)

                await server.send_message(msg)
        except Exception as e:
            print(f"Произошла ошибка при отправке почты: {e}")


database = Database(os.environ.get('DATABASE_URL'))
email_sender = EmailSender()
alembic_cfg = Config("./alembic.ini")


@asynccontextmanager
async def lifespan(_):
    # Инициализация БД
    # if not os.path.exists(os.environ.get('DATABASE_URL')):
    #     command.upgrade(alembic_cfg, "head")
    # print("Database upgraded to the latest revision.")

    yield
