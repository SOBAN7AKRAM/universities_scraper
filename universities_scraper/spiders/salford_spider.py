import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)

class SalfordSpider(scrapy.Spider):
    name = "salford_spider"
    
    def __init__(self, *args, **kwargs):
        # Starting URL for crawling
        self.start_url = "https://www.salford.ac.uk/our-staff"
        super().__init__(*args, **kwargs)
    
    def start_requests(self):
            
        yield Request(
            url=self.start_url,
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
                yield {"email": email, "university": "salford.ac.uk"}
                 # Look for the pagination next-page element.
                 
            next_page_element = await page.query_selector('.uos-pager__link[rel="next"]')
            if next_page_element:
                next_page_href = await next_page_element.get_attribute("href")
                if next_page_href:
                    # Build the absolute URL by joining with the base URL.
                    next_page_url = urljoin(self.start_url, next_page_href)
                    yield Request(
                        url=next_page_url,
                        callback=self.parse,
                        meta={
                            "playwright": True,
                            "playwright_include_page": True,
                        },
                    )
                else:
                    logger.info("Next page element found but no href attribute available.")
        finally:
            await page.close()