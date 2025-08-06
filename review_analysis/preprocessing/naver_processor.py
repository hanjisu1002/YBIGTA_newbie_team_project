import pandas as pd
import os
import re
from datetime import datetime
from database.mongodb_connection import mongo_db
from review_analysis.preprocessing.base_processor import BaseDataProcessor
from sklearn.feature_extraction.text import TfidfVectorizer

class NaverProcessor(BaseDataProcessor):
    def __init__(self, input_collection: str, output_collection: str, output_dir: str):
        super().__init__(input_path=None, output_dir=output_dir)
        
        self.input_collection = input_collection
        self.output_collection = output_collection
        
        cursor = mongo_db[self.input_collection].find({})
        data_list = list(cursor)
        self.df = pd.DataFrame(data_list)

    def preprocess(self):
        self.df.columns = self.df.columns.str.strip()

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
            
            text = text.replace("\n", " ").replace("\r", " ")
            text = re.sub(r"[^\w\s가-힣.,!?]", "", text)
            text = re.sub(r"(.)\1{2,}", r"\1\1", text)
            text = re.sub(r"\b[ㄱ-ㅎㅏ-ㅣ]{1,}\b", "", text)
            text = text.strip()

            return truncate_review(text, max_len=max_len)

        self.df["date"] = self.df["date"].apply(convert_date)
        self.df["rate"] = self.df["rate"].astype(float)
        self.df["review"] = self.df["review"].apply(clean_review)
        self.df["date"] = self.df["date"].apply(convert_date)

    def feature_engineering(self):
        self.df['weekday'] = pd.to_datetime(self.df['date'], format="%y-%m-%d", errors='coerce').dt.day_name()

        vectorizer = TfidfVectorizer(
            max_features=300,
            stop_words=None,
            token_pattern=r"(?u)\b\w+\b"
        )
        tfidf_matrix = vectorizer.fit_transform(self.df["review"])

        tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=vectorizer.get_feature_names_out())

        self.vectorizer = vectorizer
        self.tfidf_matrix = tfidf_matrix
        self.tfidf_df = tfidf_df

    def save_to_database(self):
        if hasattr(self, "df") and not self.df.empty:
            collection = mongo_db[self.output_collection]
            collection.delete_many({})
            data_list = self.df.to_dict(orient="records")
            result = collection.insert_many(data_list)
            print(f"MongoDB에 {len(result.inserted_ids)}개 문서 저장 완료: {self.output_collection}")
        else:
            print("저장할 데이터가 없습니다.")
