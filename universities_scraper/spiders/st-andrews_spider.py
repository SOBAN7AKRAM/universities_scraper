import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import logging
logger = logging.getLogger(__name__)

class StAndrewsSpider(scrapy.Spider):
    name = "st-andrews_spider"
    
    
    def start_requests(self):
        """Start with the first URL and pass along the rest in meta."""
        urls = [
            "https://www.st-andrews.ac.uk/computer-science/people/",
            "https://www.st-andrews.ac.uk/english/people/",
            "https://www.st-andrews.ac.uk/sasp/introduction/current-staff/",
            "https://www.st-andrews.ac.uk/chemistry/people/",
            "https://www.st-andrews.ac.uk/mathematics-statistics/people/",
            "https://www.st-andrews.ac.uk/physics-astronomy/people/",
            "https://www.st-andrews.ac.uk/lifelong-learning/people/",
            "https://www.st-andrews.ac.uk/history/people/",
            "https://www.st-andrews.ac.uk/psychology-neuroscience/people/",
            "https://www.st-andrews.ac.uk/geography-sustainable-development/people/",
            "https://www.st-andrews.ac.uk/biology/people/",
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
                yield {"email": email, "university": "st-andrews.ac.uk"}
            

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
    