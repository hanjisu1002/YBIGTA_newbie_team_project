# review_analysis/crawling/naver_crawler.py

from review_analysis.crawling.base_crawler import BaseCrawler
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import os
import re

class NaverCrawler(BaseCrawler):
    """
    Naver Smart Store의 제품 리뷰를 크롤링하는 클래스.

    특정 상품 URL에 접속하여, 최대 500개의 리뷰를 수집하고,
    날짜, 별점, 리뷰 본문을 포함한 데이터를 저장한다.

    Attributes:
        url (str): 크롤링 대상 Naver Smart Store 상품 페이지 URL
        reviews (list): 수집된 리뷰 데이터를 저장하는 리스트
    """

    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        self.url = "https://brand.naver.com/cocacola/products/4624572909"
        self.reviews = []

    def start_browser(self):
        """
        크롬 브라우저를 자동으로 설정 및 실행한다.

        - 자동화 탐지 방지 설정
        - 사용자 에이전트 설정
        - webdriver-manager를 이용한 크롬 드라이버 자동 설치
        """
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

        self.driver.execute_cdp_cmd(
            'Page.addScriptToEvaluateOnNewDocument',
            {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => false
                    })
                '''
            }
        )

    def scrape_reviews(self):
        """
        Naver Smart Store 리뷰를 최대 500개까지 크롤링한다.

        - 각 페이지에서 스크롤을 내려 모든 리뷰를 로드
        - 리뷰의 별점, 날짜, 본문 텍스트를 추출
        - 리뷰 수집이 완료되면 페이지를 이동하며 반복
        - '1~10 → 다음 → 11~20 → 다음 ...' 형태의 페이지 네비게이션 처리
        """
        self.start_browser()
        self.driver.get(self.url)
        time.sleep(3)

        current_page = 1

        while len(self.reviews) < 500:
            print(f"📄 {current_page} 페이지 크롤링 중...")

            # 스크롤해서 리뷰 로드 (한 페이지 내에서 전체 리뷰 로드)
            for _ in range(20):
                self.driver.execute_script("window.scrollBy(0, 3000);")
                time.sleep(1.5)

            # 별점과 리뷰 텍스트 추출

            stars = self.driver.find_elements(By.CLASS_NAME, "_15NU42F3kT")[4:]
            spans = self.driver.find_elements(By.CLASS_NAME, "_2L3vDiadT9")

            spans_text = [s.text.strip() for s in spans]  # WebElement에서 텍스트 추출
            date_pattern = re.compile(r'\d{2}\.\d{2}\.\d{2}\.')

            # 날짜 인덱스 찾기
            date_indices = [i for i, text in enumerate(spans_text) if date_pattern.fullmatch(text)]

            # 앞부분 제거
            first_index = date_indices[0]
            spans_text = spans_text[first_index:]
            date_indices = [i - first_index for i in date_indices]


            # 날짜 기준으로 분리
            groups = []
            for idx, start in enumerate(date_indices):
                end = date_indices[idx + 1] if idx + 1 < len(date_indices) else len(spans_text)
                groups.append(spans_text[start:end])

            # 한 페이지 당 20개 크롤링
            for i in range(0,19):
                try:
                    star = stars[i].text
                    date = groups[i][0]
                    content = groups[i][-2]
                    self.reviews.append([date, star, content])
                except Exception as e:
                    print(f"❌ 리뷰 {i} 파싱 실패:", e)

                    # 500개 모았으면 종료
                    if len(self.reviews) >= 500:
                        break

            # 20번째
            self.reviews.append([groups[19][0], stars[19].text, groups[19][-1]])
            

            # 다음 페이지로 이동
            try:

                if current_page%10 > 0 :
                    next_button = self.driver.find_element(By.XPATH, f'//a[text()="{current_page + 1}"]')
                    self.driver.execute_script("arguments[0].click();", next_button)
                    current_page += 1
                    time.sleep(3)
                else :
                    next_button = self.driver.find_element(By.XPATH, '//a[text()="다음"]')
                    self.driver.execute_script("arguments[0].click();", next_button)
                    current_page += 1
                    time.sleep(3)
            except Exception as e:
                print("✅ 마지막 페이지거나 '다음' 버튼 없음:", e)
                break

        self.driver.quit()



    def save_to_database(self):
        """
        수집한 리뷰 데이터를 CSV 파일로 저장한다.

        저장 경로는 초기화 시 설정된 `output_dir`에 `"naver_reviews.csv"`로 저장된다.
        파일 인코딩은 `utf-8-sig`를 사용하여 엑셀에서도 한글이 깨지지 않도록 처리함.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, "reviews_naver.csv")

        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["날짜", "별점", "리뷰"])
            writer.writerows(self.reviews)

        print(f"✅ {len(self.reviews)}개 리뷰 저장 완료: {output_path}")

