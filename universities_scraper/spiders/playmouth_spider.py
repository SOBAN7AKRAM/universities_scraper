import scrapy
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from scrapy import Request

class PlaymouthSpider(scrapy.Spider):
    name = "playmouth_spider"
    base_url = "https://www.plymouth.ac.uk/staff?lastname="
    output_folder = "urls"
    html_filename = "playmouth.txt"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        os.makedirs(self.output_folder, exist_ok=True)
        # Clear (or create) the output file at start-up.
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")
    
    def start_requests(self):
        # Start with the letter A.
        initial_letter = "A"
        url = self.base_url + initial_letter
        yield Request(
            url=url,
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_context": "university-scraper",
                "letter": initial_letter,
            },
        )
    
    async def parse(self, response):
        page = response.meta["playwright_page"]
        letter = response.meta.get("letter")
        new_links = set()
        
        try:
            content = await page.content()
            soup = BeautifulSoup(content, "lxml")
            # Extract all <a> tags that start with /staff/
            for element in soup.find_all("a"):
                href = element.get("href")
                if href and href.startswith("/staff/"):
                    absolute_href = urljoin(response.url, href)
                    new_links.add(absolute_href)
            
            if new_links:
                with open(os.path.join(self.output_folder, self.html_filename), "a", encoding="utf-8") as f:
                    for href in new_links:
                        f.write(f"{href}\n")
                self.logger.info(f"Extracted {len(new_links)} links for letter {letter}")
            else:
                self.logger.info(f"No links found for letter {letter}")
        
        
            # Compute the next letter if we haven't reached Z.
            if letter and letter < "Z":
                next_letter = chr(ord(letter) + 1)
                next_url = self.base_url + next_letter
                self.logger.info(f"Proceeding to letter {next_letter}")
                yield Request(
                    url=next_url,
                    callback=self.parse,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_context": "university-scraper",
                        "letter": next_letter,
                    },
                )
            
        finally:
            await page.close()
