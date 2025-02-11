import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

class LancasterSpider(scrapy.Spider):
    name = "lancaster_spider"
    
    def start_requests(self):
        url = "https://www.lancaster.ac.uk/lms/about-us/all-staff/"
        
            
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
            # Handle cookie consent first
            try:
                cookie_accept = await page.wait_for_selector(
                    "button#biccy-continue-button",  # Cookie accept button selector
                    state="visible",
                    timeout=10000
                )
                await cookie_accept.click()
                self.logger.info("Clicked cookie consent")
                await page.wait_for_timeout(1000)  # Wait for cookie dialog to disappear
            except PlaywrightTimeoutError:
                self.logger.info("No cookie consent found")
            
            # Extract emails before attempting to load more
            await page.wait_for_timeout(10000)  # Wait for page to load
            content = await page.content()
            emails = set(regex.findall(content))
            
            for email in emails:
                yield {"email": email, "university": "lancaster.ac.uk"}


        finally:
            await page.close()