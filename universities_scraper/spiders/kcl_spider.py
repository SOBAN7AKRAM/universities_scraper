import scrapy
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import os
from urllib.parse import urljoin

class KclSpider(scrapy.Spider):
    name = "kcl_spider"
    
    def __init__(self, *args, **kwargs):
        self.base_url = "https://www.kcl.ac.uk/"
        self.current_page = 1
        self.output_folder = "urls"
        self.html_filename = "kcl_links.txt"
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Clear (or create) the file at start-up
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")
            
        super().__init__(*args, **kwargs)
    
    def start_requests(self):
        yield Request(
            url=urljoin(self.base_url, f"people?employeeTypes=Academics&pageIndex={self.current_page}"),
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
            # Extract profile links
            profile_links = await page.query_selector_all("a[href^='/people/']")
            new_links = set()
            
            for link in profile_links:
                href = await link.get_attribute("href")
                if href and href not in existing_links:
                    new_links.add(urljoin(self.base_url, href))
            if new_links:
                with open(os.path.join(self.output_folder, self.html_filename), "a", encoding="utf-8") as f:
                    for href in new_links:
                        f.write(f"{href}\n")
                existing_links.update(new_links)
            
                    
            
            # Check if there are more pages
            self.current_page += 1
            
            # if self.current page is greater than 10, stop scraping
            if self.current_page >= 10:
                return
            
            yield Request(
                url=urljoin(self.base_url, f"people?employeeTypes=Academics&pageIndex={self.current_page}"),
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_context": "university-scraper",
                },
            )

        except PlaywrightTimeoutError:
            self.logger.error("Timeout error occurred while scraping.")
        
        finally:
            await page.close()
