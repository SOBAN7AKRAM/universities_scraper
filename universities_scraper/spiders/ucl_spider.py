import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

class UclSpider(scrapy.Spider):
    name = "ucl_spider"
    
    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs) 
        self.base_url = "https://profiles.ucl.ac.uk/"
        self.output_folder = "urls"
        self.html_filename = "ucl.txt"
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Clear (or create) the file at start-up
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")
    
    def start_requests(self):
        yield Request(
            url=urljoin(self.base_url, "search?by=text&type=user&v=staff"), 
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
            while True:
                await page.wait_for_timeout(5000)
                content = await page.content()
                soup = BeautifulSoup(content, "lxml")
                profile_links_elements = soup.select(".z0gxXryKd6kCCO3qvMQ2 a")
                for element in profile_links_elements:
                    href = element.get("href")
                    if href:  # Fixed incorrect check
                        absolute_href = urljoin(self.base_url, href)
                        new_links.add(absolute_href)
                if new_links:
                    with open(os.path.join(self.output_folder, self.html_filename), "a", encoding="utf-8") as f:
                        for href in new_links:
                            f.write(f"{href}\n")
                            
                            
                button = await page.wait_for_selector("button[aria-label='Move to the next page']", timeout=5000, state="visible")
                if button:
                    await button.click()
                else:
                    break
                
            
            
            
                
            
            

        finally:
            await page.close()
