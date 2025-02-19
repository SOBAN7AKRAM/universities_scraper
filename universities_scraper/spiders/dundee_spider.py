import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

class DundeeSpider(scrapy.Spider):
    name = "dundee_spider"
    
    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)  # Ensure proper superclass initialization
        self.base_url = "https://www.dundee.ac.uk/"
        self.start_url = "https://www.dundee.ac.uk/search"
        self.output_folder = "urls"
        self.html_filename = "dundee.txt"
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Clear (or create) the file at start-up
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")
    
    def start_requests(self):
        yield Request(
            url=urljoin(self.base_url, "search?query=%20&f%5B0%5D=staff_category_main%3A3231&f%5B1%5D=type%3Aperson"),
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_context": "university-scraper",
            },
        )
        
    async def parse(self, response):
        page = response.meta["playwright_page"]
        new_links = set()
        try:
            content = await page.content()
            soup = BeautifulSoup(content, "lxml")  # Fixed typo (soap -> sou
            profile_links_elements = soup.select(".card__title a")
            for element in profile_links_elements:
                href = element.get("href")
                if href and href.startswith("/people"):
                    absolute_href = urljoin(self.base_url, href)
                    new_links.add(absolute_href)
            if new_links:
                with open(os.path.join(self.output_folder, self.html_filename), "a", encoding="utf-8") as f:
                    for href in new_links:
                        f.write(f"{href}\n")
                        
            next_page_element = soup.select_one(".pager__item a")
            if next_page_element:
                next_page_href = next_page_element.get("href")
                if next_page_href:
                    next_page_url = urljoin(self.start_url, next_page_href)
                    await page.goto(next_page_url)
                    # yield Request(
                    #     url=next_page_url,
                    #     callback=self.parse,
                    #     meta={
                    #         "playwright": True,
                    #         "playwright_include_page": True,
                    #         "playwright_context": "university-scraper",
                    #     },
                    # )
            

        finally:
            await page.close()
