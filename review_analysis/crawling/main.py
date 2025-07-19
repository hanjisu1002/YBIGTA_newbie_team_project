import os
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class LotteOnCrawler:
    def __init__(self, output_dir: str):
        self.base_url = "https://www.lotteon.com/p/product/LM4101102508"  # 코카콜라 190ml 60캔
        self.output_dir = output_dir

    def start_browser(self):
        options = Options()
        options.add_experimental_option("detach", True)
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1920, 1080)
        self.driver.get(self.base_url)
        time.sleep(3)

    def scrape_reviews(self, max_pages=20):
        values = []
        for _ in range(max_pages):
            time.sleep(2)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            rows = soup.select('div.review_list_wrap ul li')

            for row in rows:
                date_tag = row.select_one('span.date')
                star_tag = row.select_one('div.staring em')
                review_tag = row.select_one('button.texts span.texting')

                if not (date_tag and star_tag and review_tag):
                    continue

                date = date_tag.text.strip()
                star = float(star_tag.text.strip())
                review = review_tag.get_text(separator=' ', strip=True)
                values.append([date, star, review])

            try:
                next_btn = self.driver.find_element(By.CSS_SELECTOR, 'a[class*="next"]')
                if 'disabled' in next_btn.get_attribute('class'):
                    break
                next_btn.click()
            except Exception as e:
                print("다음 버튼 클릭 실패 또는 마지막 페이지:", e)
                break

        self.reviews = values

    def save_to_database(self):
        df = pd.DataFrame(self.reviews, columns=['date', 'star_rate', 'review'])
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, 'reviews_lotteon.csv')
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
