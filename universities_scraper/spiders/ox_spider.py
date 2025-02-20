import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

class OxSpider(scrapy.Spider):
    name = "ox_spider"
    
    
    def start_requests(self):
        yield Request(
            url="https://www.brookes.ac.uk/business/about/staff",
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
        
        try:
            await page.wait_for_timeout(5000)
            content = await page.content()
            soup = BeautifulSoup(content, "lxml")  # Fixed typo (soap -> sou
            emails = regex.findall(soup.get_text())
            for email in emails:
                yield {"email": email, "university": "ox.ac.uk"}
                
        finally:
            await page.close()
