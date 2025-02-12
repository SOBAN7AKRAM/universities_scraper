import scrapy
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import os
import re
import csv

logger = logging.getLogger(__name__)

class EssexSpider(scrapy.Spider):
    name = "essex_spider"
    
    def __init__(self, *args, **kwargs):
        # Starting URL for crawling
        self.start_url = "https://www.essex.ac.uk/"
        super().__init__(*args, **kwargs)
    
    def start_requests(self):
        yield Request(
            url=urljoin(self.start_url, "people"),
            callback=self.extract_emails,
            meta={
                "playwright": True,
                "playwright_include_page": True,
            },
        )
    
    async def extract_emails(self, response):
        page = response.meta["playwright_page"]
        regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
        
        try:
            # Wait for the page to finish loading
            await page.wait_for_load_state('networkidle')
            
            # Extract the entire HTML of the page.
            content = await page.content()
            current_emails = set(regex.findall(content))
            for email in current_emails:
                yield {"email": email, "university": "essex.ac.uk"}
            
            # Look for the pagination next-page element.
            next_page_element = await page.query_selector('a:has-text("Next")')
            if next_page_element:
                next_page_href = await next_page_element.get_attribute("href")
                if next_page_href:
                    # Build the absolute URL by joining with the base URL.
                    next_page_url = urljoin(self.start_url, next_page_href)
                    logger.info(f"Navigating to next page: {next_page_url}")
                    yield Request(
                        url=next_page_url,
                        callback=self.extract_emails,
                        meta={
                            "playwright": True,
                            "playwright_include_page": True,
                        },
                    )
                else:
                    logger.info("Next page element found but no href attribute available.")
            else:
                logger.info("No next page link found.")
                
        except Exception as e:
            logger.error(f"Error processing {response.url}: {e}")
        finally:
            await page.close()