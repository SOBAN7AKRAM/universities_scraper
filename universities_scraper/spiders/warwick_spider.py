import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import logging
logger = logging.getLogger(__name__)

class WarwickSpider(scrapy.Spider):
    name = "warwick_spider"
    
    
    def start_requests(self):
        """Start with the first URL and pass along the rest in meta."""
        urls = [
            "https://warwick.ac.uk/fac/arts/history/people/staff_index/",
            "https://warwick.ac.uk/fac/sci/eng/people/",
            "https://warwick.ac.uk/fac/soc/pais/people/",
            "https://warwick.ac.uk/fac/sci/psych/people/staffprofiles/",
            "https://warwick.ac.uk/study/cll/about/cllteam/",
            "https://warwick.ac.uk/fac/sci/dcs/people/",
            "https://warwick.ac.uk/fac/sci/chemistry/staff/",
            "https://warwick.ac.uk/fac/sci/lifesci/people/",
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
            },
        )
    
    async def extract_emails(self, response):
        page = response.meta["playwright_page"]
        regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
        try:
            await page.wait_for_load_state("networkidle")
            content = await page.content()
            emails = set(regex.findall(content))
            for email in emails:
                yield {"email": email, "university": "warwick.ac.uk"}
            

        except Exception as e:
            logger.error(f"Error processing {response.url}: {e}")
            
        finally:
            await page.close()


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
                },
            )
    