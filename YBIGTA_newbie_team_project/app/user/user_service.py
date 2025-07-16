from app.user.user_repository import UserRepository
from app.user.user_schema import User, UserLogin, UserUpdate

class UserService:
    def __init__(self, userRepoitory: UserRepository) -> None:
        self.repo = userRepoitory

    # 두 dictionary를 비교해서 응답생성, 로그인 여부 결정
    def login(self, user_login: UserLogin) -> User:
        ## TODO
        user = None
        return user
        
    # 새로운 유저 등록
    def register_user(self, new_user: User) -> User:
        ## TODO
        new_user = None
        return new_user

    
    # 유저 삭제
    def delete_user(self, email: str) -> User:
        ## TODO        
        deleted_user = None
        return deleted_user

    # 유저 정보 변경
    def update_user_pwd(self, user_update: UserUpdate) -> User:
        ## TODO
        updated_user = None
        return updated_user
        