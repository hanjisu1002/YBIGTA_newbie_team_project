from argparse import ArgumentParser
from typing import Dict, Type
from base_crawler import BaseCrawler
from LotteOn_crawler import LotteOnCrawler  # ← 필요한 크롤러만 불러와

# 사용할 크롤러를 등록
CRAWLER_CLASSES: Dict[str, Type[BaseCrawler]] = {
    "lotteon": LotteOnCrawler,
}

def create_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument('-o', '--output_dir', type=str, required=True, help="Output file directory. Example: ../../database")
    parser.add_argument('-c', '--crawler', type=str, required=False, choices=CRAWLER_CLASSES.keys(),
                        help=f"Which crawler to use. Choices: {', '.join(CRAWLER_CLASSES.keys())}")
    parser.add_argument('-a', '--all', action='store_true', help="Run all crawlers. Default to False.")
    return parser

if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()

    if args.all:
        for crawler_name in CRAWLER_CLASSES.keys():
            CrawlerClass = CRAWLER_CLASSES[crawler_name]
            crawler = CrawlerClass(args.output_dir)
            crawler.start_browser()
            crawler.scrape_reviews()
            crawler.save_to_database()

    elif args.crawler:
        CrawlerClass = CRAWLER_CLASSES[args.crawler]
        crawler = CrawlerClass(args.output_dir)
        crawler.start_browser()
        crawler.scrape_reviews()
        crawler.save_to_database()

    else:
        raise ValueError("No crawler specified. Use --crawler or --all.")
