import scrapy
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup

class BradfordSpider(scrapy.Spider):
    name = "bradford_spider"
    
    def __init__(self, *args, **kwargs):
        self.output_folder = "urls"
        self.html_filename = "bradford.txt"
        os.makedirs(self.output_folder, exist_ok=True)
        self.base_url= "https://www.bradford.ac.uk/"
        
        # Clear (or create) the file at start-up
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")
            
        super().__init__(*args, **kwargs)
    
    def start_requests(self):
        """Start with the first URL and pass along the rest in meta."""
        urls = [
            "https://www.bradford.ac.uk/health/our-people/",
            "https://www.bradford.ac.uk/ei/our-people/",
            "https://www.bradford.ac.uk/law/people/",
            "https://www.bradford.ac.uk/management/som-people/"
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
        existing_links = set()
        try:
            
            
            await page.select_option("select[name='contactDT_length']", "100")
            await page.wait_for_timeout(5000)
            await page.evaluate("""
                () => {
                    const cookieDialog = document.querySelector('#onetrust-consent-sdk');
                    if (cookieDialog) {
                        cookieDialog.style.display = 'none';
                    }
                }
            """)
            # Extract profile links
            while True:
                content = await page.content()
                soup = BeautifulSoup(content, "lxml")
                profile_links = soup.select("a")
                new_links = set()

                for link in profile_links:
                    href = link.get("href")
                    if href and href not in existing_links and href.startswith("/staff"):
                        new_links.add(urljoin(self.base_url, href))

                if new_links:
                    with open(os.path.join(self.output_folder, self.html_filename), "a", encoding="utf-8") as f:
                        for href in new_links:
                            f.write(f"{href}\n")
                    existing_links.update(new_links)

                # Check if there is a next page
                next_button = await page.wait_for_selector("a:has-text('Next')")
                if next_button and not await next_button.is_disabled():
                    await next_button.click()
                    await page.wait_for_timeout(5000)
                else:
                    break
                
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

        
