import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

class UwsSpider(scrapy.Spider):
    name = "uws_spider"
    
    def start_requests(self):
        url = "https://research-portal.uws.ac.uk/en/persons/"
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
                # Extract emails before attempting to load more
                content = await page.content()
                current_emails = set(regex.findall(content))
                
                # Yield new emails with original case
                new_emails = current_emails - seen_emails
                for email in new_emails:
                    seen_emails.add(email)
                    yield {"email": email, "university": "uws.ac.uk"}

                   

        finally:
            await page.close()