import scrapy
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup  # Import BeautifulSoup

class KingstonSpider(scrapy.Spider):
    name = "kingston_spider"
    
    def __init__(self, *args, **kwargs):
        self.base_url = "https://www.kingston.ac.uk/"
        self.output_folder = "urls"
        self.html_filename = "kingston.txt"
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Clear (or create) the file at start-up
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")
            
        super().__init__(*args, **kwargs)
    
    def start_requests(self):
        url = f"staff/search-results/all/"
        yield Request(
            url=urljoin(self.base_url, url),
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_context": "university-scraper",
            },
        )
        
    async def parse(self, response):
        page = response.meta["playwright_page"]
        existing_links = set()
        
        try:
            # Wait for a specific element if needed, then get the full HTML content.
            html = await page.content()
            soup = BeautifulSoup(html, "lxml")
            
            # Extract profile links using BeautifulSoup
            profile_link_elements = soup.select(".blue-button a")
            self.logger.info(f"Found {len(profile_link_elements)} profile links.")
            
            if not profile_link_elements:
                self.logger.error("No profile links found.")
                await page.close()
                return
            
            new_links = set()
            for element in profile_link_elements:
                href = element.get("href")
                if href:
                    absolute_href = urljoin(self.base_url, href)
                    if absolute_href not in existing_links:
                        new_links.add(absolute_href)
            
            if new_links:
                with open(os.path.join(self.output_folder, self.html_filename), "a", encoding="utf-8") as f:
                    for href in new_links:
                        f.write(f"{href}\n")
                existing_links.update(new_links)
            
        except PlaywrightTimeoutError:
            self.logger.error("Timeout error occurred while scraping.")
        
        finally:
            await page.close()
