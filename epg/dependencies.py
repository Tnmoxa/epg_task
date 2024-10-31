import os
from contextlib import asynccontextmanager
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
import redis.asyncio as redis
from alembic.config import Config
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

load_dotenv()


class Database:
    """
    Класс для управления подключением к базе данных и предоставления сеансов для асинхронных операций с базой данных.

    Args:
       link (str): URL-адрес подключения к базе данных.

    Attributes:
       engine: асинхронный движок для операций с базой данных.
       _async_session: экземпляр sessionmaker для создания асинхронных сеансов.
    """

    def __init__(self, link):
        self.engine = create_async_engine(link)
        self._async_session = async_sessionmaker(self.engine, expire_on_commit=False)

    async def __call__(self):
        """
        Предоставляет сеанс для взаимодействия с базой данных.

        Yields:
          AsyncSession: асинхронный сеанс для транзакций базы данных.
        """
        async with self._async_session() as session:
            yield session


class EmailSender:
    """
    Класс для отправки уведомлений по электронной почте через SMTP-сервер.

    Attributes:
       sender (str): Адрес электронной почты, используемый для отправки писем.
       password (str): Пароль для учетной записи электронной почты отправителя.
       smtp_server (str): Адрес SMTP-сервера.
       port (int): Порт SMTP-сервера.
    """
    def __init__(self):
        self.sender = os.environ.get('SMTP_EMAIL_FROM')
        self.password = os.environ.get('SMTP_EMAIL_FROM_PASSWORD')
        self.smtp_server = os.environ.get('SMTP_SERVER')
        self.port = os.environ.get('PORT')

    async def __call__(self, recipient_email: str, message: str):
        """
        Отправляет электронное письмо указанному получателю с указанным сообщением.

        Args:
            recipient_email (str): Адрес электронной почты получателя.
            message (str): Содержимое сообщения, которое будет отправлено в электронном письме.
        """
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


# Класс хранилища redis
class Storage:
    """
    Класс для управления подключением к Redis.

    Args:
       url (str): URL-адрес подключения Redis.

    Attributes:
       client: Клиент Redis для взаимодействия с базой данных Redis.
    """
    def __init__(self, url):
        self.client = redis.from_url(url)

    async def __call__(self):
        """
        Проверяет подключение к Redis.

        Returns:
           Клиент Redis, если подключение успешно, в противном случае None.
        """
        try:
            await self.client.ping()
            return self.client
        except redis.ConnectionError:
            return None


storage = Storage(os.environ.get('REDIS_URL'))

database = Database(os.environ.get('DATABASE_URL'))
email_sender = EmailSender()
alembic_cfg = Config("./alembic.ini")


@asynccontextmanager
async def lifespan(_):
    yield
