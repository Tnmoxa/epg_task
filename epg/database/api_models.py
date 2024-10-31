import bcrypt
from fastapi import Form
from pydantic import model_validator, BaseModel, EmailStr


class User(BaseModel):
    gender: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    latitude: float
    longitude: float

    @model_validator(mode='after')
    def hash_password(self) -> 'User':
        self.set_password(self.password)
        return self

    def set_password(self, password: str):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
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
        return cls(
            gender=gender,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            longitude=longitude,
            latitude=latitude
        )
