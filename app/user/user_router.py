from fastapi import APIRouter, HTTPException, Depends, status
from app.user.user_schema import User, UserLogin, UserUpdate, UserDeleteRequest
from app.user.user_service import UserService
from app.dependencies import get_user_service
from app.responses.base_response import BaseResponse

user = APIRouter(prefix="/api/user")


@user.post("/login", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def login_user(user_login: UserLogin, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    """
    사용자 로그인

    - 입력: 이메일과 비밀번호 (`UserLogin`)
    - 처리: 이메일로 유저 조회 후 비밀번호 일치 여부 확인
    - 응답: 로그인 성공 시 유저 정보 반환
    - 예외: 유저가 존재하지 않거나 비밀번호 불일치 시 400 에러
    """
    try:
        user = service.login(user_login)
        return BaseResponse(status="success", data=user, message="Login Success.") 
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@user.post("/register", response_model=BaseResponse[User], status_code=status.HTTP_201_CREATED)
def register_user(user: User, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    """
    사용자 회원가입

    - 입력: 유저 정보 (`User`)
    - 처리: 이메일 중복 확인 후 등록
    - 응답: 등록 성공 시 유저 정보 반환
    - 예외: 이메일 중복 시 400 에러
    """
    ## TODO
    try:
        user = service.register_user(user)
        return BaseResponse(status="success", data=user, message="User registeration success.")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))



@user.delete("/delete", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def delete_user(user_delete_request: UserDeleteRequest, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    """
    사용자 삭제

    - 입력: 삭제할 유저의 이메일 (`UserDeleteRequest`)
    - 처리: 해당 이메일로 유저 존재 여부 확인 후 삭제
    - 응답: 삭제 성공 시 삭제된 유저 정보 반환
    - 예외: 유저가 존재하지 않으면 404 에러
    """
    ## TODO
    try:
        user = service.delete_user(user_delete_request.email)
        return BaseResponse(status="success", data=user, message="User Deletion Success.")
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))



@user.put("/update-password", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def update_user_password(user_update: UserUpdate, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    """
    사용자 비밀번호 변경

    - 입력: 이메일, 새 비밀번호 (`UserUpdate`)
    - 처리: 이메일로 유저 조회 후 비밀번호 변경
    - 응답: 변경된 유저 정보 반환
    - 예외: 유저가 존재하지 않으면 404 에러
    """
    ## TODO
    try:
        user = service.update_user_pwd(user_update)
        return BaseResponse(status="success", data=user, message="User password update success.")
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))