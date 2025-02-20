import scrapy
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup 

class SussexSpider(scrapy.Spider):
    name = "sussex_spider"
    
    
    def __init__(self, *args, **kwargs):
        self.output_folder = "urls"
        self.html_filename = "sussex.txt"
        self.base_url = "https://www.sussex.ac.uk/"
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Clear (or create) the file at start-up
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")
            
        super().__init__(*args, **kwargs)
    
    def start_requests(self):
        
        yield Request(
            url="https://www.sussex.ac.uk/staff/research/people/list/a-z",
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_include_page": True,
            },
        )
        
    async def parse(self, response):
        page = response.meta["playwright_page"]
        try:
            # Extract profile links
            content = await page.content()
            soup = BeautifulSoup(content, "lxml")
            new_links = set()
            profile_links = soup.select("a")
            for link in profile_links:
                href = link.get("href")
                if href and href.startswith("/staff/research/people/list/person/"):
                    new_links.add(urljoin(self.base_url, href))

            if new_links:
                with open(os.path.join(self.output_folder, self.html_filename), "a", encoding="utf-8") as f:
                    for href in new_links:
                        f.write(f"{href}\n")
                
        except PlaywrightTimeoutError:
            self.logger.error("Timeout error occurred while scraping.")
        
        finally:
            await page.close()

        
