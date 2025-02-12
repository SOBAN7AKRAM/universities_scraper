import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import logging

logger = logging.getLogger(__name__)

class CamSpider(scrapy.Spider):
    name = "cam_spider"
    
    def start_requests(self):
        """Start with the first URL and pass along the rest in meta."""
        urls = [
            "https://www.classics.cam.ac.uk/directory/faculty",
            "https://www.aha.cam.ac.uk/sd-classification/staff",
            "https://www.ames.cam.ac.uk/people/affiliated-staff",
            "https://www.divinity.cam.ac.uk/directory/teaching-officers",
            "https://www.english.cam.ac.uk/people/",
            "https://www.mmll.cam.ac.uk/faculty/staff",
            "https://www.mus.cam.ac.uk/directory/academic-research-staff",
            "https://www.phil.cam.ac.uk/people/teaching-research",
            "https://www.langcen.cam.ac.uk/staff/staff-list.html",
            "https://www.law.cam.ac.uk/people?realname=",
            "https://www.polis.cam.ac.uk/Staff_and_Students/staff",
            "https://www.vet.cam.ac.uk/directory/faculty",
            "https://www.vet.cam.ac.uk/staff-directory-1/professional-services-and-administration-staff",
            "https://www.vet.cam.ac.uk/directory/Clinicians",
            "https://www.ceb.cam.ac.uk/directory/academics",
            
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
            current_emails = set(regex.findall(content))
            for email in current_emails:
                yield {"email": email, "university": "cam.ac.uk"}

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
