import os
import time
import pandas as pd
from base_crawler import BaseCrawler  
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LotteOnCrawler(BaseCrawler):
    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        self.base_url = "https://www.lotteon.com/p/product/LD755546264"  # 코카콜라 190ml 60캔

    def start_browser(self):
        options = Options()
        options.add_experimental_option("detach", True)
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1920, 1080)
        self.driver.get(self.base_url)
        time.sleep(3)

    def scroll_until_review_loaded(self, scroll_count=5, delay=2):
        for i in range(scroll_count):
            print(f"⬇️ 스크롤 {i+1}/{scroll_count}")
            self.driver.execute_script("window.scrollBy(0, 1500);")
            time.sleep(delay)

    def wait_for_reviews(self, timeout=15):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.review_list_wrap'))
            )
            print("⏳ 리뷰 영역 감지 완료")
        except Exception as e:
            print(f"⚠️ 리뷰 로딩 실패: {e}")


    def scrape_reviews(self):
        values = []
        page = 1

        print("▶ 리뷰 영역 여러 번 스크롤 중...")
        self.scroll_until_review_loaded(scroll_count=6)

        while True:
            print(f"\n📄 {page}페이지 크롤링 중...")

            try:
                review_elements = self.driver.find_elements(By.CSS_SELECTOR, '#reviewMain > div')
            except Exception as e:
                print(f"❌ 리뷰 요소 탐색 실패: {e}")
                break

            for idx, row in enumerate(review_elements):
                try:
                    date = row.find_element(By.CSS_SELECTOR, 'span.date').text.strip()
                    star = float(row.find_element(By.CSS_SELECTOR, 'div.staring > em').text.strip())
                    review = row.find_element(By.CSS_SELECTOR, 'span.texting').text.strip()
                    values.append([date, star, review])
                except Exception:
                    continue

            print(f"📦 {page}페이지 리뷰 수집 완료, 총 수집 수: {len(values)}")

        # 다음 버튼 처리
            try:
                next_btn = self.driver.find_element(By.CSS_SELECTOR, '#reviewMain .paginationArea .next')
                if 'disabled' in next_btn.get_attribute('class'):
                    print("🚫 다음 페이지 없음 — 종료")
                    break
                self.driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(2)
                self.scroll_until_review_loaded(scroll_count=3)
                page += 1
            except Exception as e:
                print(f"❌ 다음 페이지 이동 실패: {e}")
                break

        print(f"\n✅ 총 {len(values)}개의 리뷰 수집 완료")
        self.reviews = values

    def save_to_database(self):
        if not hasattr(self, 'reviews') or not self.reviews:
            print("⚠️ 저장할 리뷰가 없습니다.")
            return

        df = pd.DataFrame(self.reviews, columns=['date', 'star_rate', 'review'])
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, 'reviews_lotteon.csv')
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"💾 저장 완료: {output_path}")
