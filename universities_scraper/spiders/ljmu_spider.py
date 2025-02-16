import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

class LmjuSpider(scrapy.Spider):
    name = "lmju_spider"
    
    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)  # Ensure proper superclass initialization
        self.base_url = "https://www.ljmu.ac.uk/"
        self.output_folder = "urls"
        self.html_filename = "lmju.txt"
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Clear (or create) the file at start-up
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")
    
    def start_requests(self):
        yield Request(
            url="https://www.ljmu.ac.uk/about-us/staff-profiles",
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
                # Try to click "load more" button
                try:
                    button = await page.wait_for_selector(
                        "a.js-staff-load-more.discoverM",
                        state="visible",
                        timeout=5000
                    )
                    
                    # Scroll and click
                    await button.scroll_into_view_if_needed()
                    await button.click()
                    
                    # Wait for new content
                    await page.wait_for_load_state("networkidle")
                    
                    
                except PlaywrightTimeoutError:
                    self.logger.info("No more results or button disabled.")
                    break
                except Exception as e:
                    self.logger.error(f"Error clicking 'Load More' button: {str(e)}")
                    break
            await page.wait_for_timeout(5000)
            content = await page.content()
            soup = BeautifulSoup(content, "lxml")  # Fixed typo (soap -> sou
            profile_links_elements = soup.find_all("a")
            for element in profile_links_elements:
                href = element.get("href")
                if href and href.startswith("/about-us/staff-profiles"):  # Fixed incorrect check
                    absolute_href = urljoin(self.base_url, href)
                    new_links.add(absolute_href)
            if new_links:
                with open(os.path.join(self.output_folder, self.html_filename), "a", encoding="utf-8") as f:
                    for href in new_links:
                        f.write(f"{href}\n")
            

        finally:
            await page.close()
