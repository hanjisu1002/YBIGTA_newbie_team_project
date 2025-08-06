import json

from typing import Dict, Optional

from app.user.user_schema import User
from app.config import USER_DATA

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[UserSchema]:
        user = self.db.query(User).filter(User.email == email).first()
        return UserSchema(**user.__dict__) if user else None

    def save_user(self, user: User) -> User: 
        self.users[user.email] = user.model_dump() # 새로운 user 정보를 dict로 저장 (기존 이메일이면 덮어쓰기) : add or overwrite
        # 새로운 유저면(이메일이 self.users에 없으면) new key 저장
        # 기존 유저면(같은 이메일이 존재) key의 value 덮어씀
        with open(USER_DATA, "w") as f:
            json.dump(self.users, f) # 전체 users를 파일에 다시 저장 (갱신)
        return user

    def delete_user(self, user: User) -> User:
        del self.users[user.email] # 해당 이메일 key 삭제
        with open(USER_DATA, "w") as f:
            json.dump(self.users, f) # 변경사항 저장
        return user