import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup

class BangorSpider(scrapy.Spider):
    name = "bangor_spider"
    
    def start_requests(self):
        url = "https://www.bangor.ac.uk/studentservices/staff.php.en"
     
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
        
        try:
            html = await page.content()
            soup = BeautifulSoup(html, "lxml")
            elements = soup.select("a[href^='mailto:']")
            for element in elements:
                email = element.get("href")
                email = re.sub(r"mailto:", "", email)
                yield {"email": email, "university": "bangor.ac.uk"}
                

        finally:
            await page.close()