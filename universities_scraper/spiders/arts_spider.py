import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

class ArtsSpider(scrapy.Spider):
    name = "arts_spider"
    
    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)  # Ensure proper superclass initialization
        self.base_url = "https://www.arts.ac.uk/"
        self.output_folder = "urls"
        self.html_filename = "arts.txt"
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Clear (or create) the file at start-up
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")
    
    def start_requests(self):
        yield Request(
            url=self.base_url,
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
            b = await page.wait_for_selector("#ccc-notify-accept")
            await b.click()

            while True:
                # Get the updated page content.
                content = await page.content()
                soup = BeautifulSoup(content, "lxml")

                # Reinitialize the set for each iteration.
                new_links = set()

                # Extract profile links from elements inside the container.
                profile_links_elements = soup.select(".results a")
                for element in profile_links_elements:
                    href = element.get("href")
                    if href:
                        new_links.add(href)

                if new_links:
                    with open(os.path.join(self.output_folder, self.html_filename), "a", encoding="utf-8") as f:
                        for href in new_links:
                            f.write(f"{href}\n")

                # Pagination
                button = await page.wait_for_selector("a[aria-label='Next page']")
                await button.click()
                await page.wait_for_timeout(5000)
        except PlaywrightTimeoutError:
            self.logger.info("No more pages to scrape.")
            
        finally:
            await page.close()
