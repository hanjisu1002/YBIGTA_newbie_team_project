import json

from typing import Dict, Optional

from app.user.user_schema import User
from app.config import USER_DATA

class UserRepository:
    def __init__(self) -> None:
        self.users: Dict[str, dict] = self._load_users() # 알고있던 user 정보 불러오기

class UserRepository:

    def _load_users(self) -> Dict[str, Dict]: # users.json 파일을 dict 형태로 불러오기 
        try:
            with open(USER_DATA, "r") as f:
                return json.load(f) # JSON 문자열을 dict로 파싱 (email → user 정보)
        except FileNotFoundError:
            raise ValueError("File not found")

    def get_user_by_email(self, email: str) -> Optional[User]:
        user = self.users.get(email) # email 키로 사용자 정보 조회 (dict에서 가져옴)
        return User(**user) if user else None # user dict → Pydantic User 객체로 변환 (없으면 None)

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