from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import Column, String
from database.mysql_connection import Base
from app.user.user_schema import User as UserSchema  # Pydantic 모델


# SQLAlchemy ORM 모델
class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    email = Column(String(100), primary_key=True, index=True)
    username = Column(String(50))  # ✅ 필드명 username으로 맞춤
    password = Column(String(100))


# Repository 클래스
class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[UserSchema]:
        user = self.db.query(User).filter(User.email == email).first()
        if user:
            return UserSchema(
                email=user.email,
                username=user.username,
                password=user.password
            )
        return None

    def save_user(self, user_data: UserSchema) -> UserSchema:
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            existing_user.username = user_data.username
            existing_user.password = user_data.password
        else:
            user = User(
                email=user_data.email,
                username=user_data.username,
                password=user_data.password
            )
            self.db.add(user)

        self.db.commit()
        return UserSchema(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password
        )

    def delete_user(self, user_data: UserSchema) -> UserSchema:
        user = self.db.query(User).filter(User.email == user_data.email).first()
        if user:
            self.db.delete(user)
            self.db.commit()
        return user_data
