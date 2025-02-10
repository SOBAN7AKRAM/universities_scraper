import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

class BrunelSpider(scrapy.Spider):
    name = "brunel_spider"
    
    def start_requests(self):
        url = "https://www.brunel.ac.uk/people" 
            
        yield Request(
                url=url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_context": "university-scraper",
                },
            )
        
    async def parse(self, response):
        page = response.meta["playwright_page"]
        regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
        seen_emails = set()
        
        try:
            self.logger.info("Waiting for form to load...")
            await page.wait_for_selector("#contactForm", timeout=5000)

            # Select "Academic" from the "Role" dropdown
            await page.select_option("#Role", value="Academic")
            self.logger.info("Selected 'Academic' from Role dropdown.")

            # Submit the form
            await page.click("#contactForm input[type='submit']")
            self.logger.info("Form submitted, waiting for results...")

            # Wait for results to update
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(20000)   
                
            content = await page.content()
            current_emails = set(regex.findall(content))
            
            # Yield new emails with original case
            new_emails = current_emails - seen_emails
            for email in new_emails:
                seen_emails.add(email)
                yield {"email": email, "university": "brunel.ac.uk"}

        finally:
            await page.close()