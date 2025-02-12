import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

class KentSpider(scrapy.Spider):
    name = "kent_spider"
    
    def start_requests(self):
        url = "https://www.kent.ac.uk/kent-business-school/people"
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
            
            # Extract email
            content = await page.content()
            current_emails = set(regex.findall(content))
            
            for email in current_emails:
                yield {"email": email, "university": "kent.ac.uk"}

        finally:
            await page.close()