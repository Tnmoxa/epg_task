import bcrypt
from pydantic import model_validator, BaseModel, EmailStr


class AuthUser(BaseModel):
    email: EmailStr
    password: str

    @model_validator(mode='after')
    def hash_password(self) -> 'AuthUser':
        self.set_password(self.password)
        return self

    def set_password(self, password: str):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
