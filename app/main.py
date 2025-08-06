import app
from fastapi import FastAPI, HTTPException, Path
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
from .user.user_router import user
from .config import PORT


# 환경변수 로드
load_dotenv()


# MongoDB 연결
mongo_url = os.getenv("MONGODB_URL")
mongo_client = MongoClient(mongo_url)
mongo_db = mongo_client.get_database("crawlingdb")

app = FastAPI()
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

app.include_router(user)

# 전처리 클래스 임포트
from review_analysis.preprocessing.emart_processor import EmartProcessor
from review_analysis.preprocessing.lotteon_processor import LotteOnProcessor
from review_analysis.preprocessing.naver_processor import NaverProcessor

PROCESSOR_MAP = {
    "emart": EmartProcessor,
    "lotteon": LotteOnProcessor,
    "naver": NaverProcessor,
}

@app.post("/review/preprocess/{site_name}")
async def preprocess(site_name: str = Path(..., description="Site name, e.g. 'emart', 'lotteon', 'naver'")):
    if site_name not in PROCESSOR_MAP:
        raise HTTPException(status_code=400, detail=f"Unknown site_name '{site_name}'")

    collection_name = f"reviews_{site_name}"
    cursor = mongo_db[collection_name].find({})
    data_list = list(cursor)

    if not data_list:
        raise HTTPException(status_code=404, detail=f"No data found in collection '{collection_name}'")

    df = pd.DataFrame(data_list)

    processor_class = PROCESSOR_MAP[site_name]
    processor = processor_class(collection_name=collection_name, output_dir="output")
    processor.df = df

    processor.preprocess()
    processor.feature_engineering()
    processor.save_to_database()

    return {
        "message": f"Preprocessing completed for {site_name}",
        "processed_records": len(processor.df),
        "tfidf_saved": f"database/tfidf_{site_name}.json"
    }

if __name__=="__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)

