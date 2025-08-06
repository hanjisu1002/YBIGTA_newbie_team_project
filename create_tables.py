from database.mysql_connection import engine, Base, DB_URL
from app.user.user_repository import User  # SQLAlchemy 모델 import

def create_tables():
    """데이터베이스 테이블을 생성합니다."""
    Base.metadata.create_all(bind=engine)
    print("테이블이 성공적으로 생성되었습니다!")

if __name__ == "__main__":
    create_tables() 


print("🔍 현재 연결된 DB 주소:", DB_URL)
