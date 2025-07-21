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
