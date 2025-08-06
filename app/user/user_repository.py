import json

from typing import Dict, Optional

from app.user.user_schema import User
from app.config import USER_DATA
from sqlalchemy.orm import Session
from sqlalchemy import Column, String
from database.mysql_connection import Base
from app.user.user_schema import User as UserSchema  # Pydantic
from typing import Optional

class User(Base):
    __tablename__ = "users"

    email = Column(String(100), primary_key=True, index=True)
    username = Column(String(50))
    password = Column(String(100))


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[UserSchema]:
        user = self.db.query(User).filter(User.email == email).first()
        return UserSchema(**user.__dict__) if user else None

    def save_user(self, user_data: UserSchema) -> UserSchema:
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            existing_user.username = user_data.username
            existing_user.password = user_data.password
        else:
            user = User(**user_data.model_dump())
            self.db.add(user)

        self.db.commit()
        return UserSchema(**user_data.model_dump())


    def delete_user(self, user_data: UserSchema) -> UserSchema:
        user = self.db.query(User).filter(User.email == user_data.email).first()
        if user:
            self.db.delete(user)
            self.db.commit()
        return user_data
