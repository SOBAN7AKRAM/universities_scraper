import scrapy
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup 

class StrathSpider(scrapy.Spider):
    name = "strath_spider"
    
    def __init__(self, *args, **kwargs):
        self.output_folder = "urls"
        self.html_filename = "strath.txt"
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Clear (or create) the file at start-up
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")
            
        super().__init__(*args, **kwargs)
    
    def start_requests(self):
        """Start with the first URL and pass along the rest in meta."""
        urls = [
            "https://www.strath.ac.uk/humanities/psychologicalscienceshealth/ourpeople/",
            "https://www.strath.ac.uk/humanities/lawschool/ourpeople/",
            "https://www.strath.ac.uk/humanities/governmentpublicpolicy/ourstaff/",
            "https://www.strath.ac.uk/humanities/meetourstaff/",
        ]
        # Start with the first URL and pass the remaining URLs in meta.
        first_url = urls[0]
        remaining_urls = urls[1:]
        
        yield Request(
            url=first_url,
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "remaining_urls": remaining_urls,
            },
        )
        
    async def parse(self, response):
        page = response.meta["playwright_page"]
        try:
            # Extract profile links
            content = await page.content()
            soup = BeautifulSoup(content, "lxml")
            new_links = set()
            profile_links = soup.select("a.faux-block-links")
            for link in profile_links:
                href = link.get("href")
                if href:
                    new_links.add(href)

            if new_links:
                with open(os.path.join(self.output_folder, self.html_filename), "a", encoding="utf-8") as f:
                    for href in new_links:
                        f.write(f"{href}\n")
                
        except PlaywrightTimeoutError:
            self.logger.error("Timeout error occurred while scraping.")
        
        finally:
            await page.close()
              
            # Retrieve the remaining URLs from meta and, if available, schedule the next request.
            remaining_urls = response.meta.get("remaining_urls", [])
            if remaining_urls:
                next_url = remaining_urls[0]
                remaining_urls = remaining_urls[1:]
                yield Request(
                    url=next_url,
                    callback=self.parse,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "remaining_urls": remaining_urls,
                    },
                )

        
