from fastapi import Depends
from app.user.user_repository import UserRepository
from app.user.user_service import UserService
from sqlalchemy.orm import Session
from database.mysql_connection import Base


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)

