from pymongo import MongoClient
from dotenv import load_dotenv
import os


# .env 로드
load_dotenv()

# 환경 변수에서 URL과 DB 이름 읽기
MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_DB = os.getenv("MONGODB_DB")

# MongoClient 인스턴스 생성
mongo_client = MongoClient(MONGODB_URL)

# 사용할 데이터베이스 객체
mongo_db = mongo_client[MONGODB_DB]