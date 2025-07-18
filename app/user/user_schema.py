from pydantic import BaseModel, EmailStr

# 사용자가 요청으로 보내는 데이터를 정의
class User(BaseModel):
    email: EmailStr
    password: str
    username: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    email: EmailStr
    new_password: str

class UserDeleteRequest(BaseModel):
    email: EmailStr

class MessageResponse(BaseModel):
    message: str

