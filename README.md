
## LotteON 리뷰 크롤링

### 크롤링 대상 사이트
- [LotteON - 코카콜라 190ml 60캔 상품 페이지](https://www.lotteon.com/p/product/LD755546264)

### 크롤링한 데이터 형식
- 총 500개의 리뷰
- CSV 파일로 저장됨 (`reviews_lotteon.csv`)
- 열(column) 구성:
  - `date`: 리뷰 작성일 (문자열)
  - `star`: 별점 (실수형, 1.0 ~ 5.0)
  - `review`: 리뷰 본문 (문자열)

###  실행 방법

```bash
# 특정 크롤러 실행
python main.py -o ./output --crawler lotteon

# 모든 크롤러 실행 (전체 병합 실행 시)
python main.py -o ./output --all



## Naver 리뷰 크롤링

(fastapi-env) (base) hanjisu@hanjisuui-MacBookAir crawling % PYTHONPATH=../../ python main.py -c naver -o ../../database

📄 1 페이지 크롤링 중...
Traceback (most recent call last):
  File "/Users/hanjisu/Desktop/YBIGTA_newbie_team_project/review_analysis/crawling/main.py", line 34, in <module>
    crawler.scrape_reviews()
  File "/Users/hanjisu/Desktop/YBIGTA_newbie_team_project/review_analysis/crawling/naver_crawler.py", line 64, in scrape_reviews
    first_index = date_indices[0]
                  ~~~~~~~~~~~~^^^
IndexError: list index out of range

위 에러가 잘 작동하는 동일한 코드를 실행하더라도 랜덤으로 발생하는데, 다시 실행하면 잘 작동됩니다. 
따라서 혹시 위와 같은 에러가 발생한다면 사이트 접근 이슈일 것으로 추정되니 조금 기다렸다가 몇 번 다시 실행해주세요 🥹

