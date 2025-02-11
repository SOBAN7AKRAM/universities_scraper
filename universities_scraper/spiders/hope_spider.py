import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

class HopeSpider(scrapy.Spider):
    name = "hope_spider"
    
    def start_requests(self):
        url = "https://www.hope.ac.uk/si/index.html"
        
            
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
        
        try:
            await page.wait_for_timeout(10000)  # Wait for page to load
            content = await page.content()
            emails = set(regex.findall(content))
            
            for email in emails:
                yield {"email": email, "university": "hope.ac.uk"}


        finally:
            await page.close()