import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# 작업 디렉토리 변경 (CSV 파일들이 있는 폴더)
os.chdir(r'C:\Users\0723a\Desktop\YBIGTA\여름 방학 세션\YBIGTA_newbie_team_project-2\database')

mongo_uri = os.getenv("MONGO_URL")
client = MongoClient(mongo_uri)
db = client['crawlingdb']

files_and_collections = [
    ('reviews_emart.csv', 'reviews_emart'),
    ('reviews_lotteon.csv', 'reviews_lotteon'),
    ('reviews_naver.csv', 'reviews_naver'),
]

for file_path, collection_name in files_and_collections:
    df = pd.read_csv(file_path)
    
    # 컬럼명 변경 (예: '날짜'->'date', '별점'->'rate', '리뷰'->'review')
    df = df.rename(columns={
        '날짜': 'date',
        '별점': 'rate',
        '리뷰': 'review'
    })
    
    data_list = df.to_dict(orient='records')
    collection = db[collection_name]
    collection.delete_many({})
    result = collection.insert_many(data_list)
    print(f"{collection_name}: {len(result.inserted_ids)} documents inserted.")
