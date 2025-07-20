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