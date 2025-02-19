import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

class WorcestorSpider(scrapy.Spider):
    name = "worcestor_spider"
    
    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)  # Ensure proper superclass initialization
        self.base_url = "https://www.worcester.ac.uk/"
        self.output_folder = "urls"
        self.html_filename = "worcestor.txt"
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Clear (or create) the file at start-up
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")
    
    def start_requests(self):
        yield Request(
            url=urljoin(self.base_url, "about/academic-schools/worcester-business-school/worcester-business-school-staff-profiles.aspx"),
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
            soup = BeautifulSoup(content, "lxml")  # Fixed typo (soap -> sou
            profile_links_elements = soup.select("#main a")
            for element in profile_links_elements:
                href = element.get("href")
                if href and href != "#":
                    new_links.add(urljoin(self.base_url, href))
            if new_links:
                with open(os.path.join(self.output_folder, self.html_filename), "a", encoding="utf-8") as f:
                    for href in new_links:
                        f.write(f"{href}\n")
                        
            

        finally:
            await page.close()
