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

# 요일 정렬을 위해 category 설정
combined_df["weekday"] = pd.Categorical(
    combined_df["weekday"],
    categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    ordered=True
)

weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# 요일별 리뷰 수 계산
weekday_count = combined_df.groupby(["weekday", "site"]).size().reset_index(name="count")

# 색상 설정
palette = {
    "Emart": "#F4DC00",   # 노랑
    "LotteON": "#FFAA0C", # 오렌지
    "Naver": "#26FB26"    # 연두
}

# 요일별 평균 리뷰 수 (사이트 구분 없이)
weekday_avg = weekday_count.groupby("weekday")["count"].mean().reset_index(name="mean_count")

# 요일 정렬
weekday_avg["weekday"] = pd.Categorical(weekday_avg["weekday"], categories=weekday_order, ordered=True)
weekday_avg = weekday_avg.sort_values("weekday")

# 전체 평균 (모든 요일 평균)
overall_mean = weekday_avg["mean_count"].mean()

# 시각화
plt.figure(figsize=(8, 5))
sns.barplot(data=weekday_avg, x="weekday", y="mean_count", color="skyblue")
plt.axhline(y=overall_mean, color="red", linestyle="--", label=f"Overall Mean: {overall_mean:.1f}")
plt.title("Average Review Count by Weekday (All Sites)")
plt.xlabel("Weekday")
plt.ylabel("Average Review Count")
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.show()
