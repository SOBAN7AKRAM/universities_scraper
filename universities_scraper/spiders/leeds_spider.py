import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup

class LeedsSpider(scrapy.Spider):
    name = "leeds_spider"
    
    def start_requests(self):
        
        url ="https://peopledevelopment.leeds.ac.uk/profiles/"
            
        yield Request(
            url=url,
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
            html = await page.content()
            soup = BeautifulSoup(html, "lxml")
            new_emails = set(re.findall(regex, soup.get_text()))
            for email in new_emails:
                seen_emails.add(email)
                yield {"email": email, "university": "leeds.ac.uk"}


        finally:
            await page.close()