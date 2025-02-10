import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

class PortSpider(scrapy.Spider):
    name = "aub_spider"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_emails = set()  # Store extracted emails globally
        self.current_page = 1  # Start from page 1

    def start_requests(self):
        """Start with the first page only."""
        yield Request(
            url=f"https://staff.aub.ac.uk/en?type=academic&page=1",
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_context": "university-scraper",
                "page_no": 1  # Track current page
            },
        )
        
    async def parse(self, response):
        """Extract emails and then load the next page."""
        page = response.meta["playwright_page"]
        page_no = response.meta["page_no"]
        regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

        try:
            self.logger.info(f"Scraping Page {page_no}...")

            # Wait for page to fully load
            await page.wait_for_load_state("networkidle")


            # Extract emails
            content = await page.content()
            current_emails = set(regex.findall(content))

            # Yield only new emails
            new_emails = current_emails - self.seen_emails
            for email in new_emails:
                self.seen_emails.add(email)
                yield {"email": email, "university": "aub.ac.uk"}

            # Close page after scraping
            await page.close()

            # Call the next page
            if page_no < 10:  # Update this with your limit
                next_page = page_no + 1
                self.logger.info(f"Moving to next page: {next_page}")
                yield Request(
                    url=f"https://staff.aub.ac.uk/en?type=academic&page={next_page}",
                    callback=self.parse,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_context": "university-scraper",
                        "page_no": next_page,
                    },
                )

        except PlaywrightTimeoutError:
            self.logger.error(f"Timeout error on Page {page_no}")
