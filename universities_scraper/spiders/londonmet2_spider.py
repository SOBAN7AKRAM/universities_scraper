import scrapy
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import os
import re
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)  # Create a logger

class Londenmet2Spider(scrapy.Spider):
    name = "londonmet2_spider"

    def __init__(self, *args, **kwargs):
        self.output_folder = "urls"
        self.html_filename = "londonmet.txt"
        self.seen_emails = set()  # Store extracted emails to avoid duplicates

        self.file_path = os.path.join(self.output_folder, self.html_filename)

        # Read URLs from the file
        if not os.path.exists(self.file_path):
            self.logger.error("URL file not found. Make sure bathspa_links.txt exists.")
            self.profile_links = []
        else:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.profile_links = [line.strip() for line in f.readlines() if line.strip()]

        super().__init__(*args, **kwargs)

    def start_requests(self):
        """Visit each profile URL one by one."""
        first_url = self.profile_links[0]
        remaining_urls = self.profile_links[1:]
        
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
            html = await page.content()
            email = set(regex.findall(html))
            if email:
                yield {"email": email, "university": "londonmet.ac.uk"}
                
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
