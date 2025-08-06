from database.mysql_connection import engine, Base
from app.user.user_schema import User

def create_tables():
    """데이터베이스 테이블을 생성합니다."""
    Base.metadata.create_all(engine)
    print("테이블이 성공적으로 생성되었습니다!")

if __name__ == "__main__":
    create_tables() 