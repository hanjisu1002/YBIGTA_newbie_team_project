import os
import time
import pandas as pd
from .base_crawler import BaseCrawler  
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


class LotteOnCrawler(BaseCrawler):
    """
    LotteON 페이지에서 리뷰를 수집하는 크롤러 클래스.

    - 대상 URL: 코카콜라 190ml 60캔 제품 페이지
    - Selenium을 사용하여 페이지를 열고 리뷰를 수집
    - 최대 500개의 리뷰를 수집하면 자동 종료
    - 수집된 정보는 날짜, 평점, 리뷰글로 구성되어 CSV 파일로 저장

    Attributes:
        output_dir (str): 리뷰 데이터를 저장할 디렉토리 경로
        base_url (str): 크롤링할 대상 상품 페이지 URL
    """

    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        self.base_url = "https://www.lotteon.com/p/product/LD755546264"

    def start_browser(self):
        """BaseCrawler의 추상 메서드 구현: 크롬 브라우저 실행"""
        options = Options()
        options.add_experimental_option("detach", True)
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1920, 1080)

    def scroll_until_review_loaded(self, scroll_count=5, delay=2):
        for _ in range(scroll_count):
            self.driver.execute_script("window.scrollBy(0, 1500);")
            time.sleep(delay)

    def scrape_reviews(self):
        self.start_browser()
        self.driver.get(self.base_url)
        time.sleep(3)

        values = []
        page = 1

        self.scroll_until_review_loaded(scroll_count=6)

        while True:
            try:
                review_elements = self.driver.find_elements(By.CSS_SELECTOR, '#reviewMain > div')
            except Exception as e:
                print(f"리뷰 요소 탐색 실패: {e}")
                break

            for row in review_elements:
                try:
                    date = row.find_element(By.CSS_SELECTOR, 'span.date').text.strip()
                    star = float(row.find_element(By.CSS_SELECTOR, 'div.staring > em').text.strip())
                    review = row.find_element(By.CSS_SELECTOR, 'span.texting').text.strip().replace('\n', ' ').replace('\r', ' ')
                    values.append([date, star, review])

                    if len(values) >= 500:
                        print("500개 리뷰 수집 완료")
                        self.reviews = values
                        self.driver.quit()
                        return
                except Exception:
                    continue

            try:
                next_btn = self.driver.find_element(By.CSS_SELECTOR, '#reviewMain .paginationArea .next')
                if 'disabled' in next_btn.get_attribute('class'):
                    print("다음 페이지 없음 — 종료")
                    break
                self.driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(2)
                self.scroll_until_review_loaded(scroll_count=3)
                page += 1
            except Exception as e:
                print(f"다음 페이지 이동 실패: {e}")
                break

        self.driver.quit()
        self.reviews = values

    def save_to_database(self):
        if not hasattr(self, 'reviews') or not self.reviews:
            print("저장할 리뷰가 없습니다.")
            return

        df = pd.DataFrame(self.reviews, columns=['date', 'rate', 'review'])
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, 'reviews_lotteon.csv')
        df.to_csv(output_path, index=False, encoding='utf-8-sig', lineterminator='\n')
        print(f"저장 완료: {output_path}")
