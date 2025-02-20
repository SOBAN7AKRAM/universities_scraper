import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class EdSpider(scrapy.Spider):
    name = "ed_spider"
    base_url = "https://search.ed.ac.uk/"
    
    
    def start_requests(self):
            
            yield Request(
                url=urljoin(self.base_url, "?q=academic+staff&search=emails"),
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_context": "university-scraper",
                },
            )
        
    async def parse(self, response):
        page = response.meta["playwright_page"]
        regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
        seen_emails = set()
        
        try:
            content = await page.content()
            soup = BeautifulSoup(content, "lxml")
            elements = regex.findall(soup.get_text())
            for element in elements:
                yield {"email": element, "university": "ed.ac.uk"}
                
            next_page_element = soup.select_one("a[aria-label='next']")
            if next_page_element:
                next_page_url = urljoin(self.base_url, next_page_element["href"])
                yield Request(
                    url=next_page_url,
                    callback=self.parse,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_context": "university-scraper",
                    },
                )

        finally:
            await page.close()