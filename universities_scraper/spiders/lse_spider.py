import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

class LseSpider(scrapy.Spider):
    name = "lse_spider"
    
    def start_requests(self):
        url = "https://www.lse.ac.uk/people/search-people?typeOfStaff=0%2F1%2F284%2F313%2F314"
        
            
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
            while True:
                # Extract emails before attempting to load more
                content = await page.content()
                current_emails = set(regex.findall(content))
                
                # Yield new emails with original case
                new_emails = current_emails - seen_emails
                for email in new_emails:
                    seen_emails.add(email)
                    yield {"email": email, "university": "lse.ac.uk"}

                # Try to click "Show more" button
                try:
                    button = await page.wait_for_selector(
                        'button[aria-label^="Go to next page"]',
                        state="visible",
                        timeout=2000
                    )
                    
                    # Scroll and click
                    await button.scroll_into_view_if_needed()
                    await button.click()
                    
                    # Wait for new content
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(2000)  # Wait for new content to load
                except PlaywrightTimeoutError:
                    self.logger.info("No more results or button disabled")
                    break
                except Exception as e:
                    self.logger.error(f"Error clicking button: {str(e)}")
                    break

        finally:
            await page.close()