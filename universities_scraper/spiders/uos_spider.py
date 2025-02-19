import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

class UosSpider(scrapy.Spider):
    name = "uos_spider"
    
    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)  # Ensure proper superclass initialization
        self.base_url = "https://www.uos.ac.uk/"
        self.output_folder = "urls"
        self.html_filename = "uos.txt"
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Clear (or create) the file at start-up
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")
    
    def start_requests(self):
        yield Request(
            url=urljoin(self.base_url, "about/get-in-touch/people-directory/"),
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
            b = await page.wait_for_selector("#ccc-close")
            await b.click()
            
            
            # Wait for the select element to be available.
            await page.wait_for_selector("select#type")
            # Select the "Academic Staff" option by its value.
            await page.select_option("select#type", value="academic staff")
            # Wait for the dynamic content to update after selecting.
            await page.wait_for_timeout(3000)  # Adjust timeout as needed

            while True:
                # Get the updated page content.
                content = await page.content()
                soup = BeautifulSoup(content, "lxml")

                # Reinitialize the set for each iteration.
                new_links = set()

                # Extract profile links from elements inside the container.
                profile_links_elements = soup.select(".profile-card__body a")
                for element in profile_links_elements:
                    href = element.get("href")
                    if href:
                        absolute_href = urljoin(self.base_url, href)
                        new_links.add(absolute_href)

                if new_links:
                    with open(os.path.join(self.output_folder, self.html_filename), "a", encoding="utf-8") as f:
                        for href in new_links:
                            f.write(f"{href}\n")

                # Pagination: Find the anchor with the ">" text.
                button = await page.wait_for_selector("a:has-text('>')")
                await button.click()
                await page.wait_for_timeout(5000)
        except PlaywrightTimeoutError:
            self.logger.info("No more pages to scrape.")
            
        finally:
            await page.close()
