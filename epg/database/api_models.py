import bcrypt
from fastapi import Form
from pydantic import model_validator, BaseModel, EmailStr


class User(BaseModel):
    """
    Представляет модель пользователя с полями для личной информации и методами хеширования и проверки паролей.

    Attributes:
        gender (str): Пол пользователя.
        first_name (str): Имя пользователя.
        last_name (str): Фамилия пользователя.
        email (EmailStr): Адрес электронной почты пользователя.
        password (str): Пароль пользователя (будет хеширован).
        latitude (float): Координата широты местоположения пользователя.
        longitude (float): Координата долготы местоположения пользователя.
    """

    gender: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    latitude: float
    longitude: float

    @model_validator(mode='after')
    def hash_password(self) -> 'User':
        """
        Автоматически хеширует пароль пользователя после проверки.

        Returns:
            User: Экземпляр пользователя с хешированным паролем.
        """
        self.set_password(self.password)
        return self

    def set_password(self, password: str):
        """
        Хеширует предоставленный пароль и сохраняет его в атрибуте пароля.

        Args:
            password (str): текстовый пароль для хеширования.
        """
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Проверяет, совпадает ли предоставленный пароль с хешированным паролем.

        Args:
            password (str): текстовый пароль для проверки.
            hashed_password (str): хешированный пароль для сравнения.

        Returns:
            bool: True, если пароль совпадает, False в противном случае.
        """

        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    @classmethod
    def as_form(
            cls,
            gender: str = Form(...),
            first_name: str = Form(...),
            last_name: str = Form(...),
            email: EmailStr = Form(...),
            password: str = Form(...),
            latitude: float = Form(...),
            longitude: float = Form(...),
    ):
        """
        Создает экземпляр User из полей данных формы, обеспечивая совместимость отправки форм в FastAPI.

        Args:
            gender (str): Пол пользователя.
            first_name (str): Имя пользователя.
            last_name (str): Фамилия пользователя.
            email (EmailStr): Адрес электронной почты пользователя.
            password (str): Пароль пользователя (будет хеширован).
            latitude (float): Координата широты местоположения пользователя.
            longitude (float): Координата долготы местоположения пользователя.

        Returns:
            User: Экземпляр модели User, заполненный данными формы.
        """
        return cls(
            gender=gender,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            longitude=longitude,
            latitude=latitude
        )
