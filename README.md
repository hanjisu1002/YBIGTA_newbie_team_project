
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
따라서 혹시 위와 같은 에러가 발생한다면 사이트 접근 이슈일 것으로 추정되니 조금 기다렸다가 몇 번 다시 실행해주세요 

## EDA 과정
EDA: 개별 사이트에 대한 시각화 및 설명
크롤링한 리뷰 데이터를 기반으로 세 개의 플랫폼(Emart, LotteON, Naver)에 대해 다음과 같은 시각화를 진행하였습니다:

1. 별점 분포 (Rating Distribution)
각 사이트 및 전체 데이터를 기준으로 별점의 개수를 **막대그래프(Bar Plot)**로 시각화했습니다.
공통적으로 5점과 4점에 데이터가 집중되어 있었습니다. 이상치로 분류될만한 데이터는 없었습니다.

2. 날짜 분포 (Review Date Distribution)
리뷰 날짜가 다양하게 존재하여, 년도-월 단위로 집계한 월별 리뷰 개수 시각화하였습니다.
Emart와 LotteON은 특정 기간에 리뷰가 집중되었습니다.
Naver의 경우 초기 크롤링 시 날짜 누락 및 비정상 데이터 확인되어 전처리 과정에서 데이터를 정제하는 것의 필요성을 느꼈습니다.

3. 텍스트 길이 분포 (Review Length Distribution)
리뷰의 길이(len(review))를 기준으로 박스플롯(Box Plot) 시각화하였습니다.
대부분 40자~100자 이내의 분포를 보이며, 200자 이상은 이상치로 판단하였습니다.
Naver의 경우에는 초기 크롤링 시 비정상 데이터로 확인되어 전처리 과정에서 데이터를 정제하는 것의 필요성을 느꼈습니다.

## 전처리/FE
1. naver에서 크롤링한 csv파일의 경우에는 비정상 데이터로 저장이 되어있어 이를 우리가 사용할 수 있는 정제된 데이터로 바꾸는 과정을 거쳤습니다. 또한 크롤링 과정에서 csv파일의 header부분을 통일하지 않아 그 부분을 통일햇습니다.

2. 텍스트 데이터 전처리
리뷰 데이터는 텍스트 형태이기 때문에 모델 학습에 적합하게 정제하는 과정이 필요하다고 판단하여 clean_review() 함수를 통해 다음과 같은 전처리를 수행하였습니다
-줄바꿈 문자 제거
리뷰 텍스트 내 \n, \r 등의 줄바꿈 문자를 제거하여 한 줄로 정리된 형태로 만들었습니다.
text = text.replace("\n", " ").replace("\r", " ")

-특수기호 제거
한글, 영문, 숫자, 공백, 일부 문장 부호(.,!? 등)를 제외한 특수문자를 정규표현식으로 제거했습니다.
text = re.sub(r"[^\w\s가-힣.,!?]", "", text)

-중복 문자 축약
사용자 리뷰에는 "굿!!!!", "최고오오오오"처럼 동일 문자가 반복되는 경우가 많습니다. 이를 2회까지만 허용하고 축약하여 단어의 형태를 정돈했습니다.
text = re.sub(r"(.)\1{2,}", r"\1\1")

-단독 자음/모음 제거
단독 자음/모음의 경우 노이즈로 작용할 수 있어 단독 자음·모음을 제거했습니다.
text = re.sub(r"\b[ㄱ-ㅎㅏ-ㅣ]{1,}\b", "", text)

-공백 제거
문자열 양 끝의 불필요한 공백을 제거합니다.
text = text.strip()

-텍스트 길이 자르기
최종적으로 최대 길이를 제한하기 위해 truncate_review() 함수를 호출하였습니다. 기본적으로 최대 100자, 최소 80자 이상이 되도록 끊어주며 공백 단위로 끊기 때문에 단어가 어색하게 잘리지 않습니다.

3. 날짜 전처리
크롤링된 날짜 데이터는 포맷이 사이트마다 달랐습니다.
예: 23.01.01, 2023-01-01, 2023.1.1. 등 다양한 형태
이를 모두 yy-mm-dd 형식으로 통일하여 처리하였습니다.
변환 과정에서 날짜 파싱에 실패한 경우는 결측값으로 처리했습니다.
dt = datetime.strptime(date_str, fmt)
return dt.strftime("%y-%m-%d")

4. 파생 변수 생성
날짜를 기반으로 weekday 파생 변수를 생성했습니다.

해당 리뷰가 무슨 요일에 작성되었는지를 파악할 수 있으며, 이는 사용자 행태 분석이나 시계열 패턴 분석에 활용할 수 있습니다.
self.df['weekday'] = pd.to_datetime(self.df['date'], format="%y-%m-%d", errors='coerce').dt.day_name()

5. 이상치 및 결측치 처리
리뷰 텍스트가 없는 경우 "" (빈 문자열)로 처리하였습니다.
날짜 파싱에 실패한 경우에는 NaT로 저장되며 이후 분석 시 제외 가능하도록 처리하였습니다.
텍스트 길이 기준 이상치는 200자 이상으로 판단하고 박스플롯으로 확인하였으며,
추후 필요시 제거하거나 별도 분석 대상으로 활용 가능합니다.



