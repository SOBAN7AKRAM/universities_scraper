import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

class BathSpider(scrapy.Spider):
    name = "bath_spider"
    
    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs) 
        self.base_url = "https://www.bath.ac.uk/"
        self.start_url = "https://www.bath.ac.uk/profiles/"
        self.output_folder = "urls"
        self.html_filename = "bath.txt"
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Clear (or create) the file at start-up
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")
    
    def start_requests(self):
        yield Request(
            url=urljoin(self.start_url, "?f.Type%7CY=Academic+profile"), 
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_context": "university-scraper",
            },
        )
        
    async def parse(self, response):
        page = response.meta["playwright_page"]
        new_links = set()
        try:
            content = await page.content()
            soup = BeautifulSoup(content, "lxml")
            profile_links_elements = soup.find_all("a")
            for element in profile_links_elements:
                href = element.get("href")
                if href and href.startswith("/s/"):
                    absolute_href = urljoin(self.base_url, href)
                    new_links.add(absolute_href)
            if new_links:
                with open(os.path.join(self.output_folder, self.html_filename), "a", encoding="utf-8") as f:
                    for href in new_links:
                        f.write(f"{href}\n")
            
            # Click the next button
            next_button = soup.find("a", text="Next ›")
            if next_button:
                href = next_button.get("href")
                if href:
                    yield Request(
                        url=urljoin(self.start_url, href),
                        callback=self.parse,
                        meta={
                            "playwright": True,
                            "playwright_include_page": True,
                            "playwright_context": "university-scraper",
                        },
                    )
            
        finally:
            await page.close()
