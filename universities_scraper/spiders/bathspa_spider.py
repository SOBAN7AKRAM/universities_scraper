import scrapy
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import os
from urllib.parse import urljoin

class BathspaSpider(scrapy.Spider):
    name = "bathspa_spider"
    
    def __init__(self, *args, **kwargs):
        self.start_url = "https://www.bathspa.ac.uk/search-results"
        self.output_folder = "urls"
        self.html_filename = "bathspa_links.txt"
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Clear (or create) the file at start-up
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")
            
        super().__init__(*args, **kwargs)
    
    def start_requests(self):
        url = '?searchStudioQuery=&isGrid=false&facets=fq%3Dsectiontype_s%3A%22profile%22%26fq%3Dprofiletype_ss%3A%22Academic%2520staff%22&orderBy=&start=0'
        yield Request(
            url=urljoin(self.start_url, url),
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
            while True:
                # Extract profile links
                profile_links = await page.query_selector_all(".title a.stretched-link")
                new_links = set()
                
                for link in profile_links:
                    href = await link.get_attribute("href")
                    if href and href not in existing_links:
                        new_links.add(href)

                if new_links:
                    with open(os.path.join(self.output_folder, self.html_filename), "a", encoding="utf-8") as f:
                        for href in new_links:
                            f.write(f"{href}\n")
                    existing_links.update(new_links)
              
                        
                
                # Handle pagination
                next_page = await page.query_selector("a[aria-label='Next']")
                if next_page:
                    await next_page.click()
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(5000)
                else:
                    break

        except PlaywrightTimeoutError:
            self.logger.error("Timeout error occurred while scraping.")
        
        finally:
            await page.close()
