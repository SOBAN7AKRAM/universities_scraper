import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class CardiffmetSpider(scrapy.Spider):
    name = "cardiffmet_spider"
    
    def start_requests(self):
        """Start with the first URL and pass along the rest in meta."""
        urls = [
            "https://www.cardiffmet.ac.uk/technologies/staff-profiles/Pages/default.aspx",
            "https://www.cardiffmet.ac.uk/about/ltdu/Pages/Staff-Information.aspx",
            "https://www.cardiffmet.ac.uk/business/Pages/Meet-the-Team.aspx",
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
            content = await page.content()
            soup = BeautifulSoup(content, "lxml")
            current_emails = regex.findall(soup.get_text())
            for email in current_emails:
                yield {"email": email, "university": "cardiffmet.ac.uk"}

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
