import scrapy
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import os
import re
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)  # Create a logger

class tSpider(scrapy.Spider):
    name = "t_spider"

    def start_requests(self):
        
        yield Request(
            url="https://www.sofascore.com/basketball",
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
            # button = await page.query_selector("button[aria-label='Show contact details']")
            # button.click()
            # await page.wait_for_timeout(1000)
            
            
            html = await page.content()
                
        
            
        except Exception as e:
            logger.error(f"Error processing {response.url}: {e}")

        finally:
            await page.close()

