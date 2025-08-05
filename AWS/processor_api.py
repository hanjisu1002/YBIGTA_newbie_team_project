from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from AWS.mongodb_connection import mongo_db
from review_analysis.preprocessing.emart_processor import EmartProcessor
from review_analysis.preprocessing.lotteon_processor import LotteOnProcessor
from review_analysis.preprocessing.naver_processor import NaverProcessor

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        "processed_records": len(processor.df)
    }
