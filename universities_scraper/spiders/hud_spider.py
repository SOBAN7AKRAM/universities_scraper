import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

class HudSpider(scrapy.Spider):
    name = "hud_spider"
    
    
    def start_requests(self):
        yield Request(
            url="https://www.hud.ac.uk/about/schools/huddersfield-business-school/about-us/our-structure-and-people/a-to-z/",
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
            overlay = await page.query_selector("#ccc-overlay")
            if overlay:
                await overlay.evaluate("element => element.style.display = 'none'")

            
            while True:
                # Try to click "load more" button
                try:
                    button = await page.wait_for_selector(
                        "button:has-text('Show more')",
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
            emails = regex.findall(soup.get_text())
            for email in emails:
                yield {"email": email, "university": "hud.ac.uk"}
            

        finally:
            await page.close()
