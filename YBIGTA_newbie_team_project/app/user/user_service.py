from app.user.user_repository import UserRepository
from app.user.user_schema import User, UserLogin, UserUpdate

class UserService:
    def __init__(self, userRepoitory: UserRepository) -> None:
        self.repo = userRepoitory

    # 두 dictionary를 비교해서 응답생성, 로그인 여부 결정
    def login(self, user_login: UserLogin) -> User:
        ## TODO
         """
        사용자 로그인 정보를 받아 로그인 처리를 수행합니다.

        Args:
            user_login (UserLogin): 로그인할 사용자의 이메일과 비밀번호 정보

        Returns:
            User: 로그인에 성공한 사용자 정보

        Raises:
            ValueError: 이메일이 존재하지 않을 때
            ValueError: 비밀번호가 틀렸을 때
        """
        user = self.repo.get_user_by_email(user_login.email)
        if user is None:
            raise ValueError("User not Found.")
        if user.password != user_login.password:
            raise ValueError("Invalid PW")
        return user
        
    # 새로운 유저 등록
    def register_user(self, new_user: User) -> User:
        ## TODO
        """
        새로운 사용자를 등록합니다.

        Args:
            new_user (User): 회원가입할 사용자의 이메일, 비밀번호, 이름 정보

        Returns:
            User: 회원가입에 성공한 사용자 정보

        Raises:
            ValueError: 이미 동일한 이메일이 존재할 때
        """
        existing_user = self.repo.get_user_by_email(new_user.email)          
        if existing_user is not None:
            raise ValueError("User already Exists.")
        self.repo.save_user(new_user)
        return new_user

    
    # 유저 삭제
    def delete_user(self, email: str) -> User:
        ## TODO    
        """
        이메일을 받아 해당 사용자를 삭제(탈퇴)합니다.

        Args:
            email (str): 탈퇴할 사용자의 이메일

        Returns:
            User: 삭제된 사용자 정보

        Raises:
            ValueError: 이메일이 존재하지 않을 때
        """    
        deleted_user = self.repo.get_user_by_email(email)          
        if deleted_user is None:
            raise ValueError("User not Found.")
        self.repo.delete_user(deleted_user)
        return deleted_user

    # 유저 정보 변경
    def update_user_pwd(self, user_update: UserUpdate) -> User:
        ## TODO
        """
        사용자의 비밀번호를 새 값으로 변경합니다.

        Args:
            user_update (UserUpdate): 이메일과 새 비밀번호 정보

        Returns:
            User: 비밀번호 변경이 완료된 사용자 정보

        Raises:
            ValueError: 이메일이 존재하지 않을 때
        """
        updated_user = self.repo.get_user_by_email(user_update.email)
        if updated_user is None:
            raise ValueError("User not Found")
        updated_user.password = user_update.new_password
        self.repo.save_user(updated_user)
        return updated_user
        