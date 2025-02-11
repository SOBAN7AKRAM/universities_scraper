import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from urllib.parse import urljoin

class NapierSpider(scrapy.Spider):
    name = "napier_spider"
    base_url = "https://www.napier.ac.uk"

    def start_requests(self):
        # Start at page 1 (no explicit page parameter means page 1)
        url = urljoin(self.base_url, "people?t0sz=100&tab=0")
        yield Request(
            url=url,
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_context": "university-scraper",
                "current_page": 1,  # starting page
            },
        )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
        current_page = response.meta.get("current_page", 1)
        
        try:
            # Handle cookie consent first.
            try:
                # Wait for the popup element to appear.
                cookie = await page.wait_for_selector(".truste_cm_outerdiv", timeout=10000)
                # Directly set the element's display style to 'none'.
                await cookie.evaluate("el => el.style.display = 'none'")
                self.logger.info("Cookie popup hidden via element evaluation.")
                await page.wait_for_timeout(1000)  # Wait for the popup to be hidden
                
                
                dis = await page.wait_for_selector(".truste_overlay", timeout=2000)
                # Directly set the element's display style to 'none'.
                await dis.evaluate("el => el.style.display = 'none'")
                await page.wait_for_timeout(1000)  # Wait for the popup to be hidden
            except PlaywrightTimeoutError:
                self.logger.info("No cookie consent found")
                
            
                
            # Extract emails from the current page
            content = await page.content()
            current_emails = set(regex.findall(content))
            for email in current_emails:
                yield {"email": email, "university": "napier.ac.uk"}
                
            # Determine the next page number
            next_page_number = current_page + 1
            
            if current_emails:
                yield Request(
                        url=urljoin(self.base_url, f"people?t0sz=100&tab=0&tabpg0={next_page_number}#rms"),
                        callback=self.parse,
                        meta={
                            "playwright": True,
                            "playwright_include_page": True,
                            "playwright_context": "university-scraper",
                            "current_page": next_page_number,  # starting page
                        },
                    )
            
            else:
                self.logger.info("No next page link found for data-page value "
                                 f"{next_page_number}.")

        finally:
            await page.close()


