    
        
import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class GcuSpider(scrapy.Spider):
    name = "gcu_spider"
    
    def start_requests(self):
        """Start with the first URL and pass along the rest in meta."""
        urls = [
            "https://www.gcu.ac.uk/aboutgcu/academicschools/gsbs/staff",
            "https://www.gcu.ac.uk/aboutgcu/academicschools/cebe/staff/",
            "https://www.gcu.ac.uk/aboutgcu/academicschools/hls/staff",
        ]
        # Start with the first URL and pass the remaining URLs in meta.
        first_url = urls[0]
        remaining_urls = urls[1:]
        
        yield Request(
            url=first_url,
            callback=self.extract_emails,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "remaining_urls": remaining_urls,
                "current_url": first_url,
            },
        )
    
    async def extract_emails(self, response):
        page = response.meta["playwright_page"]
        regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

        try:  
            await page.wait_for_load_state('networkidle')
            content = await page.content()
            current_emails = set(regex.findall(content))
            for email in current_emails:
                yield {"email": email, "university": "gcu.ac.uk"}

        except Exception as e:
            logger.error(f"Error processing {response.url}: {e}")

        finally:
            await page.close()
            
        # check if it had pagination
        try:
            next_page_element = await page.query_selector('.pagination-next') 
            if next_page_element:
                next_page_href = await next_page_element.get_attribute("href")
                if next_page_href:
                        # Build the absolute URL using urljoin.
                        next_url = urljoin(response.meta.get("current_url"), next_page_href)
                        self.logger.info(f"Navigating to next page: {next_url}")
                        yield Request(
                            url=next_url,
                            callback=self.extract_emails,
                            meta={
                                "playwright": True,
                                "playwright_include_page": True,
                                "current_url": response.meta.get("current_url"),
                            },
                        )
                else:
                    self.logger.info("Next page element found but no href attribute available.")
        except Exception as e:
            self.logger.error(f"Error processing pagination: {str(e)}")
            

        # Retrieve the remaining URLs from meta and, if available, schedule the next request.
        remaining_urls = response.meta.get("remaining_urls", [])
        if remaining_urls:
            next_url = remaining_urls[0]
            remaining_urls = remaining_urls[1:]
            yield Request(
                url=next_url,
                callback=self.extract_emails,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "remaining_urls": remaining_urls,
                    "current_url": next_url,
                },
            )
