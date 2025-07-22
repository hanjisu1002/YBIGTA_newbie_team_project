import pandas as pd
import os
import re
from datetime import datetime
from review_analysis.preprocessing.base_processor import BaseDataProcessor
from sklearn.feature_extraction.text import TfidfVectorizer

class ExampleProcessor(BaseDataProcessor):
    def __init__(self, input_path: str, output_path: str):
        super().__init__(input_path, output_path)
        self.df = pd.read_csv(self.input_path)

    def preprocess(self):
        self.df.columns = self.df.columns.str.strip()

        # 사이트별 컬럼명 변경
        if "naver" in self.input_path:
            self.df.rename(columns={"별점": "rate", "날짜": "date", "리뷰": "review"}, inplace=True)
        elif "emart" in self.input_path:
            self.df.rename(columns={"평점": "rate", "작성일": "date", "내용": "review"}, inplace=True)
        elif "lotteon" in self.input_path:
            self.df.rename(columns={"점수": "rate", "날짜": "date", "리뷰내용": "review"}, inplace=True)

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

        # 날짜 변환
        self.df["date"] = self.df["date"].apply(convert_date)

       

    def feature_engineering(self):
        print("🧪 feature_engineering 실행됨")
        print("✅ 리뷰 개수:", len(self.df))
        print("✅ Null 리뷰 개수:", self.df["review"].isnull().sum())
        print("✅ 예시 리뷰:", self.df["review"].head(1).values)
         # 날짜 처리 및 요일 파생 변수 생성
        self.df['weekday'] = pd.to_datetime(self.df['date'], format="%y-%m-%d", errors='coerce').dt.day_name()


        # TF-IDF 벡터화
        vectorizer = TfidfVectorizer(
            max_features=300,
            stop_words=None,
            token_pattern=r"(?u)\b\w+\b"
        )
        tfidf_matrix = vectorizer.fit_transform(self.df["review"])

        # 저장을 위해 DataFrame으로 변환
        tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=vectorizer.get_feature_names_out())

        # 기존 self.df와 합치기
        self.df = pd.concat([self.df.reset_index(drop=True), tfidf_df.reset_index(drop=True)], axis=1)

        print("✅ 최종 컬럼 수:", len(self.df.columns))
        print("✅ 마지막 5개 컬럼:", self.df.columns[-5:])


        # 저장을 위해 보관
        self.vectorizer = vectorizer
        self.tfidf_matrix = tfidf_matrix
    
    def save_to_database(self):
        if "naver" in self.input_path:
            site_name = "naver"
        elif "emart" in self.input_path:
            site_name = "emart"
        elif "lotteon" in self.input_path:
            site_name = "lotteon"
        else:
            raise ValueError("Unknown site in input_path")

        filename = f"preprocessed_reviews_{site_name}.csv"
        save_path = os.path.join(self.output_dir, filename)
        self.df.to_csv(save_path, index=False)
    