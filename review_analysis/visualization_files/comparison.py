import pandas as pd
import matplotlib.pyplot as plt
import platform
import seaborn as sns



def keyword_comparison(df):
    # TF-IDF 컬럼만 따로 추출
    tfidf_cols = df.columns[~df.columns.isin(['rate', 'date', 'review', 'weekday'])]
    tfidf_df = df[tfidf_cols]


    # 시각화 스타일 지정
    sns.set_style("whitegrid")
    sns.set_palette("muted")

    # 시스템별 폰트 설정
    if platform.system() == 'Darwin':  # macOS
        plt.rcParams['font.family'] = 'Apple SD Gothic Neo'
    elif platform.system() == 'Windows':
        plt.rcParams['font.family'] = 'Malgun Gothic'
    else:  # Linux
        plt.rcParams['font.family'] = 'NanumGothic'

    plt.rcParams['axes.unicode_minus'] = False  # 마이너스 깨짐 방지



    # 평균 TF-IDF가 높은 단어 상위 N개
    top_n = 20
    mean_tfidf = tfidf_df.mean().sort_values(ascending=False).head(top_n)



    plt.figure(figsize=(10, 6))
    mean_tfidf.sort_values().plot(kind='barh', color='skyblue', edgecolor='black')
    plt.title(f"{site.capitalize()} - Top 20 TF-IDF 단어", fontsize=16)
    plt.xlabel("TF-IDF 점수", fontsize=12)
    plt.ylabel("단어", fontsize=12)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.tight_layout()
    plt.show()
    return None

for site in ["naver", "lotteon", "emart"]:
    df = pd.read_csv(f"database/preprocessed_reviews_{site}.csv")
    print(f"{site.capitalize()} 리뷰 시각화")
    keyword_comparison(df)
