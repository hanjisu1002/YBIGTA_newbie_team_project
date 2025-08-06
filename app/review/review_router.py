from fastapi import APIRouter, HTTPException, Path
from typing import Dict, Type, cast
from database.mongodb_connection import mongo_db
from pydantic import BaseModel
import pandas as pd

from review_analysis.preprocessing.base_processor import BaseDataProcessor
from review_analysis.preprocessing.naver_processor import NaverProcessor
from review_analysis.preprocessing.emart_processor import EmartProcessor
from review_analysis.preprocessing.lotteon_processor import LotteOnProcessor

PREPROCESS_CLASSES: Dict[str, Type[BaseDataProcessor]] = {
    "reviews_naver": cast(Type[BaseDataProcessor], NaverProcessor),
    "reviews_emart": cast(Type[BaseDataProcessor], EmartProcessor),
    "reviews_lotteon": cast(Type[BaseDataProcessor], LotteOnProcessor),
}

router = APIRouter()

@router.post("/review/preprocess/{site_name}")
def preprocess_review(site_name: str = Path(..., description="사이트 이름 (예: reviews_naver, reviews_emart, reviews_lotteon)")
):
    if site_name not in PREPROCESS_CLASSES:
        raise HTTPException(status_code=400, detail="Unknown site_name")

    # MongoDB에서 크롤링 데이터 불러오기
    raw_collection = mongo_db[f"reviews_{site_name}"]
    raw_data = list(raw_collection.find({}))

    if not raw_data:
        raise HTTPException(status_code=404, detail="No data found in MongoDB")

    df = pd.DataFrame(raw_data)

    # 전처리
    processor = PREPROCESS_CLASSES[site_name]()
    processed_df = processor.preprocess(df)
    processor.mongo_collection = mongo_db["tfidf_results"]
    # TF-IDF 벡터화 및 MongoDB 저장
    processor.feature_engineering()

    # 기존 데이터 삭제 
    mongo_db[f"preprocessed_{site_name}"].delete_many({})

    # 전처리된 데이터 저장
    mongo_db[f"preprocessed_{site_name}"].insert_many(processed_df.to_dict("records"))

    return {"message": f"{site_name} 데이터 전처리 완료", "count": len(processed_df)}
