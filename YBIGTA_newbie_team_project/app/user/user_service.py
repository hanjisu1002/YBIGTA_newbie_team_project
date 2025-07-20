from app.user.user_repository import UserRepository
from app.user.user_schema import User, UserLogin, UserUpdate

class UserService:
    def __init__(self, userRepoitory: UserRepository) -> None:
        self.repo = userRepoitory

    # 두 dictionary를 비교해서 응답생성, 로그인 여부 결정
    def login(self, user_login: UserLogin) -> User:
        ## TODO
        user = self.repo.get_user_by_email(user_login.email)
        if user is None:
            raise ValueError("User not Found.")
        if user.password != user_login.password:
            raise ValueError("Invalid PW")
        return user
        
    # 새로운 유저 등록
    def register_user(self, new_user: User) -> User:
        ## TODO
        existing_user = self.repo.get_user_by_email(new_user.email)          
        if existing_user is not None:
            raise ValueError("User already Exists.")
        self.repo.save_user(new_user)
        return new_user

    
    # 유저 삭제
    def delete_user(self, email: str) -> User:
        ## TODO        
        deleted_user = self.repo.get_user_by_email(email)          
        if deleted_user is None:
            raise ValueError("User not Found.")
        self.repo.delete_user(deleted_user)
        return deleted_user

    # 유저 정보 변경
    def update_user_pwd(self, user_update: UserUpdate) -> User:
        ## TODO
        updated_user = self.repo.get_user_by_email(user_update.email)
        if updated_user is None:
            raise ValueError("User not Found")
        updated_user.password = user_update.new_password
        self.repo.save_user(updated_user)
        return updated_user
        