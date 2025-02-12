import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

class SolentSpider(scrapy.Spider):
    name = "solent_spider"
    
    def start_requests(self):
        url = "https://www.solent.ac.uk/staff?page=1&role=0-1259-1601-1609-1610"
            
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
        
        try:
            await page.wait_for_load_state("networkidle")
            overlay = await page.wait_for_selector("#ccc-overlay", state="visible", timeout=5000)
            await overlay.evaluate("el => el.style.display = 'none'")
            
            while True:
                # Extract emails before attempting to load more
                content = await page.content()
                current_emails = set(regex.findall(content))
                
                for email in current_emails:
                    yield {"email": email, "university": "solent.ac.uk"}

                # Try to click "Show more" button
                try:
                    button = await page.wait_for_selector(
                        "button[aria-label^='Next page']",
                        state="visible",
                        timeout=5000
                    )
                    
                    # Scroll and click
                    await button.scroll_into_view_if_needed()
                    await button.click()
                    
                    # Wait for new content
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(5000)  # Wait for new content to load
                except PlaywrightTimeoutError:
                    self.logger.info("No more results or button disabled")
                    break
                except Exception as e:
                    self.logger.error(f"Error clicking button: {str(e)}")
                    break

        finally:
            await page.close()