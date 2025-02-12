import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import logging
logger = logging.getLogger(__name__)

class ReadingSpider(scrapy.Spider):
    name = "reading_spider"
    
    
    def start_requests(self):
        """Start with the first URL and pass along the rest in meta."""
        urls = [
            "https://www.reading.ac.uk/economics/our-staff",
            "https://www.reading.ac.uk/ges/staff",
            "https://www.reading.ac.uk/history/our-staff",
            "https://www.reading.ac.uk/computer-science/staff",
            "https://www.reading.ac.uk/scfp/staff",
            "https://www.reading.ac.uk/education/staff",
        ]
        # Start with the first URL and pass the remaining URLs in meta.
        first_url = urls[0]
        remaining_urls = urls[1:]
        
        yield Request(
            url=first_url,
            callback=self.extract_emails,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "remaining_urls": remaining_urls,
            },
        )
    
    async def extract_emails(self, response):
        page = response.meta["playwright_page"]
        regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
        try:
            await page.wait_for_load_state("networkidle")
            content = await page.content()
            emails = set(regex.findall(content))
            for email in emails:
                yield {"email": email, "university": "reading.ac.uk"}
            

        except Exception as e:
            logger.error(f"Error processing {response.url}: {e}")
            
        finally:
            await page.close()


        # Retrieve the remaining URLs from meta and, if available, schedule the next request.
        remaining_urls = response.meta.get("remaining_urls", [])
        if remaining_urls:
            next_url = remaining_urls[0]
            remaining_urls = remaining_urls[1:]
            yield Request(
                url=next_url,
                callback=self.extract_emails,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "remaining_urls": remaining_urls,
                },
            )
    