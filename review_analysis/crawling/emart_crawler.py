from review_analysis.crawling.base_crawler import BaseCrawler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import csv


class EmartCrawler(BaseCrawler):
    """
    Emart 상품 리뷰를 크롤링하는 클래스.
    SSG.COM 내 Emart 상품 페이지에서 Selenium과 BeautifulSoup을 활용해
    날짜, 평점, 리뷰 텍스트를 수집하고 CSV로 저장합니다.

    수집 필드: 날짜(date), 평점(rate), 리뷰 내용(review)

    Attributes:
        output_dir (str): CSV 파일을 저장할 경로
        max_page (int): 크롤링할 최대 페이지 수 (기본값: 50)
    """

    def __init__(self, output_dir: str, max_page: int = 50):
        super().__init__(output_dir)
        self.url = "https://emart.ssg.com/item/itemView.ssg?itemId=1000529473806&siteNo=6001&ckwhere=danawa&appPopYn=n&utm_medium=PCS&utm_source=danawa&utm_campaign=danawa_pcs&service_id=estimatedn"  
        self.max_page = max_page
        self.columns = ['date', 'rate', 'review']
        self.values: list[list[str]] = []
        self.driver = None
        self.driver = self._start_browser()

    def _start_browser(self):
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        return driver

    def start_browser(self):
        pass

    def scrape_reviews(self):
        self.driver.get(self.url)
        self.driver.implicitly_wait(3)

        for page in range(1, self.max_page + 1):
            print(f"{page}페이지 크롤링 중...")

            try:
                self.driver.execute_script("fn_GoCommentPage(arguments[0])", page)
                time.sleep(2)
            except Exception as e:
                print(f"{page}페이지 이동 실패: {e}")
                break

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            data_rows = soup.find_all('li', attrs={'class': 'rvw_expansion_panel v2'})

            for row in data_rows:
                blank = []

                date = row.find('div', class_='rvw_item_label rvw_item_date')
                blank.append(date.get_text(strip=True).replace('\n', ' ') if date else "날짜 없음")

                rate = row.find('em')
                blank.append(rate.get_text(strip=True).replace('\n', ' ') if rate else "별점 없음")

                text = row.find('p', class_='rvw_item_text')
                review = text.get_text(strip=True).replace('\n', ' ') if text else "리뷰 없음"
                review = review.replace('\r', ' ')
                blank.append(review)

                self.values.append(blank)

        self.driver.quit()
        print("크롤링 완료")

    def save_to_database(self) -> None:
        os.makedirs(self.output_dir, exist_ok=True)
        df = pd.DataFrame(self.values, columns=self.columns)
        output_file = os.path.join(self.output_dir, "reviews_emart.csv")
        df.to_csv(output_file, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
        print(f"저장 완료: {output_file}")