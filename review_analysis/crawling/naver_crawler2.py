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
    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        self.url = "https://brand.naver.com/cocacola/products/4624572909"
        self.reviews = []

    def start_browser(self):
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
            stars = self.driver.find_elements(By.CLASS_NAME, "_15NU42F3kT")[4:-1]
            spans = self.driver.find_elements(By.CLASS_NAME, "_2L3vDiadT9")

            spans_text = [s.text.strip() for s in spans]  # WebElement에서 텍스트 추출
            print(spans_text)
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


            # 결과 확인
            for g in groups:
                print("🧩", g)


            for i in range(0,19):
                try:
                    star = stars[i].text
                    date = groups[i][0]
                    content = groups[i][-2]
                    self.reviews.append([date, star, content])
                    print(f"{len(self.reviews)}️⃣ {date} | {star}점 | {content[:30]}")
                except Exception as e:
                    print(f"❌ 리뷰 {i} 파싱 실패:", e)

                    # 500개 모았으면 종료
                    if len(self.reviews) >= 500:
                        break

            

            # 다음 페이지로 이동
            try:
                if current_page%10 > 0 :
                    next_button = self.driver.find_element(By.XPATH, f'//a[text()="{(current_page%10) + 1}"]')
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
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, "naver_reviews.csv")

        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["날짜", "별점", "리뷰"])
            writer.writerows(self.reviews)

        print(f"✅ {len(self.reviews)}개 리뷰 저장 완료: {output_path}")