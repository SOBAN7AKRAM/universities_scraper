import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

class UweSpider(scrapy.Spider):
    name = "uwe_spider"
    
    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)  # Ensure proper superclass initialization
        self.base_url = "https://people.uwe.ac.uk/"
        self.output_folder = "urls"
        self.html_filename = "uwe.txt"
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Clear (or create) the file at start-up
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")
    
    def start_requests(self):
        yield Request(
            url=urljoin(self.base_url, "SearchResults?query=a"),
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
                # Get the updated page content.
                content = await page.content()
                soup = BeautifulSoup(content, "lxml")

                # Extract profile links from elements inside the container.
                profile_links_elements = soup.select("a")
                for element in profile_links_elements:
                    href = element.get("href")
                    if href and href.startswith('/Person'):
                        new_links.add(urljoin(self.base_url, href))

                if new_links:
                    with open(os.path.join(self.output_folder, self.html_filename), "a", encoding="utf-8") as f:
                        for href in new_links:
                            f.write(f"{href}\n")

        except PlaywrightTimeoutError:
            self.logger.info("No more pages to scrape.")
            
        finally:
            await page.close()
