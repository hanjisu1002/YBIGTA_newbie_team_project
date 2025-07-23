import os
import glob
from argparse import ArgumentParser
from typing import Dict, Type, cast
from review_analysis.preprocessing.base_processor import BaseDataProcessor
from review_analysis.preprocessing.naver_processor import NaverProcessor
from review_analysis.preprocessing.emart_processor import EmartProcessor
from review_analysis.preprocessing.lotteon_processor import LotteOnProcessor



# 모든 preprocessing 클래스를 예시 형식으로 적어주세요. 
# key는 "reviews_사이트이름"으로, value는 해당 처리를 위한 클래스
PREPROCESS_CLASSES: Dict[str, Type[BaseDataProcessor]] = {
    "reviews_naver": cast(Type[BaseDataProcessor], NaverProcessor),
    "reviews_emart": cast(Type[BaseDataProcessor], EmartProcessor),
    "reviews_lotteon": cast(Type[BaseDataProcessor], NaverProcessor),
}

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
DATABASE_DIR = os.path.join(PROJECT_ROOT, "database")
REVIEW_COLLECTIONS = glob.glob(os.path.join(DATABASE_DIR, "reviews_*.csv"))

def create_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument('-o', '--output_dir', type=str, required=False, default = "../../database", help="Output file dir. Example: ../../database")
    parser.add_argument('-c', '--preprocessor', type=str, required=False, choices=PREPROCESS_CLASSES.keys(),
                        help=f"Which processor to use. Choices: {', '.join(PREPROCESS_CLASSES.keys())}")
    parser.add_argument('-a', '--all', action='store_true',
                        help="Run all data preprocessors. Default to False.")    
    return parser

if __name__ == "__main__":

    parser = create_parser()
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    if args.all: 
        print("✅ 전체 데이터 전처리 시작") 
        for csv_file in REVIEW_COLLECTIONS:
            base_name = os.path.splitext(os.path.basename(csv_file))[0]
            print(f"📄 현재 파일: {base_name}") 
            for key in PREPROCESS_CLASSES.keys():
                if base_name.startswith(key):  
                    print(f"🔧 처리 시작: {key}") 
                    preprocessor_class = PREPROCESS_CLASSES[key]
                    preprocessor = preprocessor_class(csv_file, args.output_dir)
                    preprocessor.preprocess()
                    print(f"✅ preprocess 완료: {csv_file}")
                    preprocessor.feature_engineering()
                    print(f"✅ feature_engineering 완료: {csv_file}")
                    preprocessor.save_to_database()
                    print(f"✅ 저장 완료: {csv_file}")
                    break

