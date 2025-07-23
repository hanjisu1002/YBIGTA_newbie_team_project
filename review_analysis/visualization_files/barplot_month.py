import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 데이터 준비
naver_df = pd.read_csv("/Users/hanjisu/Desktop/YBIGTA_newbie_team_project/database/preprocessed_reviews_naver.csv")
lotteon_df = pd.read_csv("/Users/hanjisu/Desktop/YBIGTA_newbie_team_project/database/preprocessed_reviews_lotteon.csv")
emart_df = pd.read_csv("/Users/hanjisu/Desktop/YBIGTA_newbie_team_project/database/preprocessed_reviews_emart.csv")

# 사이트 정보 추가
naver_df["site"] = "Naver"
lotteon_df["site"] = "LotteON"
emart_df["site"] = "Emart"

# 병합
combined_df = pd.concat([naver_df, lotteon_df, emart_df], ignore_index=True)

# 날짜 형식 변환 및 month 컬럼 생성
combined_df["date"] = pd.to_datetime(combined_df["date"], format="%y-%m-%d", errors="coerce")
combined_df["month"] = combined_df["date"].dt.to_period("M").astype(str)

# 월별 리뷰 수 계산
monthly_count = combined_df.groupby(["month", "site"]).size().reset_index(name="count")


# 색상 설정
palette = {
    "Emart": "#F4DC00",   # 노랑
    "LotteON": "#FFAA0C", # 오렌지
    "Naver": "#26FB26"    # 연두
}

# 그래프
plt.figure(figsize=(12, 6))
sns.lineplot(data=monthly_count, x="month", y="count", hue="site", marker="o", palette=palette)
plt.title("Monthly Review Count by Site (YYYY-MM)")
plt.xlabel("Month")
plt.ylabel("Number of Reviews")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
