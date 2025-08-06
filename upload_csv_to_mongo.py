import pandas as pd
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# MongoDB 연결
mongo_url = os.getenv("MONGODB_URL")
if not mongo_url or "mongodb" in mongo_url:
    mongo_url = "mongodb://admin:adminpass@localhost:27017/crawlingdb?authSource=admin"
mongo_client = MongoClient(mongo_url)
mongo_db = mongo_client.get_database("crawlingdb")

def upload_csv_to_mongo(csv_file_path, collection_name):
    """CSV 파일을 MongoDB에 업로드"""
    try:
        # CSV 파일 읽기
        df = pd.read_csv(csv_file_path)
        print(f"CSV 파일 읽기 완료: {csv_file_path}")
        print(f"데이터 개수: {len(df)}")
        
        # DataFrame을 딕셔너리 리스트로 변환
        data_list = df.to_dict(orient="records")
        
        # MongoDB 컬렉션에 삽입
        collection = mongo_db[collection_name]
        result = collection.insert_many(data_list)
        
        print(f"MongoDB 업로드 완료: {collection_name}")
        print(f"업로드된 문서 수: {len(result.inserted_ids)}")
        
        return True
    except Exception as e:
        print(f"오류 발생: {e}")
        return False

def main():
    # 업로드할 CSV 파일들
    csv_files = [
        ("database/reviews_emart.csv", "reviews_emart"),
        ("database/reviews_lotteon.csv", "reviews_lotteon"),
        ("database/reviews_naver.csv", "reviews_naver")
    ]
    
    for csv_file, collection_name in csv_files:
        if os.path.exists(csv_file):
            print(f"\n=== {csv_file} 업로드 중 ===")
            upload_csv_to_mongo(csv_file, collection_name)
        else:
            print(f"파일이 존재하지 않습니다: {csv_file}")

if __name__ == "__main__":
    main() 