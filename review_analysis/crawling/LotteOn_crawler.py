import os
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LotteOnCrawler:
    def __init__(self, output_dir: str):
        self.base_url = "https://www.lotteon.com/p/product/LD755546264"  # 코카콜라 190ml 60캔
        self.output_dir = output_dir

    def start_browser(self):
        options = Options()
        options.add_experimental_option("detach", True)
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1920, 1080)
        self.driver.get(self.base_url)
        time.sleep(3)

    def scrape_reviews(self):
        values = []
        print("리뷰 영역 로딩 대기 중...")

        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.list_review'))
        )

        for page in range(1, 11):  # 10페이지까지
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            review_items = soup.select('ul.list_review > li')

            for row in review_items:
                # 날짜
                date_tag = row.select_one('.underAction .date')
                # 별점
                star_tag = row.select_one('.staring em')
                # 리뷰글
                review_tag = row.select_one('.texting')

                if not (date_tag and star_tag and review_tag):
                    continue

                date = date_tag.text.strip()
                star = float(star_tag.text.strip())
                review = review_tag.get_text(separator=' ', strip=True)

                values.append([date, star, review])

            print(f"{page}페이지 완료")

            try:
                next_button = self.driver.find_element(By.XPATH, f'//a/span[text()="{page+1}"]')
                self.driver.execute_script("arguments[0].click();", next_button)
                time.sleep(2)
            except:
                print("다음 페이지 없음")
                break

        self.reviews = values

    def save_to_database(self):
        df = pd.DataFrame(self.reviews, columns=['date', 'star_rate', 'review'])
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, 'reviews_lotteon.csv')
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
