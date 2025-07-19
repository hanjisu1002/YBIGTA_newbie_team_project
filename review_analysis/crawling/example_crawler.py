from base_crawler import BaseCrawler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import os

class ExampleCrawler(BaseCrawler):
    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        self.base_url = 'https://m.11st.co.kr/products/ma/4217186886?&trTypeCd=MAS112&trCtgrNo=950076&checkCtlgPrd=false'
        
    def start_browser(self):
        options = Options()
        options.add_experimental_option("detach", True)
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.get(self.base_url)
            self.driver.implicitly_wait(2)
        except Exception as e:
            print("브라우저 실행 실패:", e)
    
    def scrape_reviews(self):
        columns = ['date', 'star_rate', 'review']
        values = []
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        data_rows = soup.find_all('li', attrs={'class': 'item'})

        for i, row in enumerate(data_rows):
            print(f'[{i+1}] 코카콜라 11번가 리뷰 크롤링')
            blank = []

            date_box = row.find('div', attrs={'class': 'c-card-review__other'})
            if date_box and date_box.find('span'):
                date = date_box.find('span').get_text().strip()
                blank.append(date)
            else:
                blank.append('Something is wrong')
                print('날짜 가져올때 문제발생')
                continue

            star = row.find('span', attrs={'class': 'c-starrate__gauge'})
            if star:
                style = star.get('style')
                if style:
                    percent = style.replace('width:', '').replace('%', '').replace(';', '').strip()
                    star_rate = round(float(percent) / 20, 2)
                    blank.append(star_rate)
                else:
                    blank.append('Something is wrong')
                    print('별점 가져올때 문제발생')
                    continue

            review = row.find('p', attrs={'class': 'c-card-review__text'})
            if review:
                review = review.get_text().strip()
                blank.append(review)
            else:
                blank.append('Something is wrong')
                print('리뷰 가져올때 문제발생')
                continue

            values.append(blank)
            print('---------------------------------------------------')

        self.reviews = values
    
    def save_to_database(self):
        df = pd.DataFrame(self.reviews, columns=['date', 'star_rate', 'review'])
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, 'reviews_list.csv')
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
