from sqlite3 import IntegrityError

import bcrypt

from sqlalchemy import select
from epg.database import storage_models as sm

from pydantic import model_validator, BaseModel, EmailStr, ValidationError
from epg.dependencies import database as db


class User(BaseModel):
    avatar: str
    gender: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str

    @model_validator(mode='after')
    def hash_password(self) -> 'User':
        self.set_password(self.password)
        return self

    def set_password(self, password: str):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
