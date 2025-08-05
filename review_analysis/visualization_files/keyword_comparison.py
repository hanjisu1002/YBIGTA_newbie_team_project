import pandas as pd
import matplotlib.pyplot as plt
import platform
import seaborn as sns



import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import platform


def keyword_comparison(site: str, json_dir="output"):
    # JSON 경로
    json_path = f"{json_dir}/tfidf_{site}.json"

    # JSON 로드
    with open(json_path, "r", encoding="utf-8") as f:
        tfidf_data = json.load(f)

    # DataFrame으로 변환
    tfidf_df = pd.DataFrame(tfidf_data)

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

    # 시각화
    plt.figure(figsize=(10, 6))
    mean_tfidf.sort_values().plot(kind='barh', color='skyblue', edgecolor='black')
    plt.title(f"{site.capitalize()} - Top {top_n} TF-IDF 단어", fontsize=16)
    plt.xlabel("TF-IDF 점수", fontsize=12)
    plt.ylabel("단어", fontsize=12)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.tight_layout()
    plt.show()

for site in ["naver", "lotteon", "emart"]:
    print(f"{site.capitalize()} 리뷰 시각화")
    keyword_comparison(site)
