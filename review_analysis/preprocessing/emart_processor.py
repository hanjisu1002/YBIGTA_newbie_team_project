import pandas as pd
import os
os.chdir(r'C:\Users\0723a\Desktop\YBIGTA\여름 방학 세션\YBIGTA_newbie_team_project-2')

import re
import json
from datetime import datetime
from database.mongodb_connection import mongo_db
from review_analysis.preprocessing.base_processor import BaseDataProcessor
from sklearn.feature_extraction.text import TfidfVectorizer

class EmartProcessor(BaseDataProcessor):
    def __init__(self, collection_name: str, output_dir: str):
        super().__init__(input_path=None, output_dir=output_dir)
        
        # MongoDB에서 데이터 읽기
        cursor = mongo_db[collection_name].find({})
        data_list = list(cursor)
        self.df = pd.DataFrame(data_list)
        self.collection_name = collection_name  # 멤버 변수로 저장

    def preprocess(self):
        self.df.columns = self.df.columns.str.strip()

        # 날짜 변환 함수
        def convert_date(date_str):
            try:
                date_str = date_str.strip()
                if date_str.endswith("."):
                    date_str = date_str[:-1]

                for fmt in ["%y.%m.%d", "%y-%m-%d", "%Y-%m-%d", "%Y.%m.%d"]:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        return dt.strftime("%y-%m-%d")
                    except ValueError:
                        continue
                return None
            except:
                return None
            
        def truncate_review(text, max_len=100, min_len=80):
            if len(text) <= max_len:
                return text

            cut_text = text[:max_len]
            last_space = cut_text.rfind(" ")

            if last_space >= min_len:
                return cut_text[:last_space]
            else:
                return cut_text

        def clean_review(text, max_len=100):
            if not isinstance(text, str):
                return ""
            
            # 줄바꿈 제거
            text = text.replace("\n", " ").replace("\r", " ")

            # 특수기호 제거 
            text = re.sub(r"[^\w\s가-힣.,!?]", "", text)

            # 중복 문자 줄이기
            text = re.sub(r"(.)\1{2,}", r"\1\1", text)

            # 자음/모음 단독 제거
            text = re.sub(r"\b[ㄱ-ㅎㅏ-ㅣ]{1,}\b", "", text)
            
            text = text.strip()

            return truncate_review(text, max_len=max_len)

        # 날짜 변환
        self.df["date"] = self.df["date"].apply(convert_date)
        
        # 별점 float로 변환
        self.df["rate"] = self.df["rate"].astype(float)
    
        # 리뷰 전처리
        self.df["review"] = self.df["review"].apply(clean_review)

        # 날짜 변환 (중복 호출 제거 가능하지만 유지)
        self.df["date"] = self.df["date"].apply(convert_date)

    def feature_engineering(self):
        # 날짜 처리 및 요일 파생 변수 생성
        self.df['weekday'] = pd.to_datetime(self.df['date'], format="%y-%m-%d", errors='coerce').dt.day_name()

        # TF-IDF 벡터화
        vectorizer = TfidfVectorizer(
            max_features=300,
            stop_words=None,
            token_pattern=r"(?u)\b\w+\b"
        )
        tfidf_matrix = vectorizer.fit_transform(self.df["review"])

        # DataFrame 변환
        tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=vectorizer.get_feature_names_out())

        # 저장용 보관
        self.vectorizer = vectorizer
        self.tfidf_matrix = tfidf_matrix
        self.tfidf_df = tfidf_df

    def save_to_database(self):
        if hasattr(self, "df") and not self.df.empty:
            collection_name = getattr(self, "collection_name", None)
            if collection_name is None:
                collection_name = "reviews_emart"

            collection = mongo_db[collection_name]

            # 기존 데이터 삭제 (옵션)
            collection.delete_many({})

            # DataFrame을 딕셔너리 리스트로 변환하여 삽입
            data_list = self.df.to_dict(orient="records")
            result = collection.insert_many(data_list)
            print(f"MongoDB에 {len(result.inserted_ids)}개 문서 저장 완료: {collection_name}")
        else:

            print("저장할 데이터가 없습니다.")

