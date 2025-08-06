from fastapi import APIRouter, HTTPException, Path, Query
from typing import Dict, Type, cast
from database.mongodb_connection import mongo_db
import pandas as pd

from review_analysis.preprocessing.base_processor import BaseDataProcessor
from review_analysis.preprocessing.naver_processor import NaverProcessor
from review_analysis.preprocessing.emart_processor import EmartProcessor
from review_analysis.preprocessing.lotteon_processor import LotteOnProcessor

# site_name 간단명칭으로 매핑
PREPROCESS_CLASSES: Dict[str, Type[BaseDataProcessor]] = {
    "naver": cast(Type[BaseDataProcessor], NaverProcessor),
    "emart": cast(Type[BaseDataProcessor], EmartProcessor),
    "lotteon": cast(Type[BaseDataProcessor], LotteOnProcessor),
}

router = APIRouter()

@router.post("/review/preprocess/{site_name}")
def preprocess_review(site_name: str = Path(..., description="사이트 이름 (예: naver, emart, lotteon)")):
    if site_name not in PREPROCESS_CLASSES:
        raise HTTPException(status_code=400, detail="Unknown site_name")

    raw_collection_name = f"reviews_{site_name}"               # 원본 데이터 컬렉션명
    processed_collection_name = f"preprocessed_{site_name}"   # 전처리 결과 저장 컬렉션명

    raw_collection = mongo_db[raw_collection_name]
    raw_data = list(raw_collection.find({}))

    if not raw_data:
        raise HTTPException(status_code=404, detail=f"No data found in MongoDB collection: {raw_collection_name}")

    output_dir = "./output"  # 필요에 따라 환경변수로 관리 가능

    processor_class = PREPROCESS_CLASSES[site_name]
    processor = processor_class(
        input_collection=raw_collection_name,
        output_collection=processed_collection_name,
        output_dir=output_dir,
    )

    processor.preprocess()
    processor.feature_engineering()
    processor.save_to_database()

    return {"message": f"{site_name} 데이터 전처리 완료", "count": len(processor.df)}


@router.get("/review/collection_status")
def collection_status(collection_name: str = Query(..., description="확인할 컬렉션명")):
    collections = mongo_db.list_collection_names()
    if collection_name not in collections:
        return {
            "collection_exists": False,
            "message": f"'{collection_name}' 컬렉션이 존재하지 않습니다.",
            "collections": collections,
        }

    count = mongo_db[collection_name].count_documents({})
    return {
        "collection_exists": True,
        "collection_name": collection_name,
        "document_count": count,
        "collections": collections,
    }
