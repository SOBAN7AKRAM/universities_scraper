
import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import logging

logger = logging.getLogger(__name__)

class CardiffSpider(scrapy.Spider):
    name = "cardiff_spider"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_emails = set()  # Store extracted emails globally
        self.base_url = "https://www.cardiff.ac.uk"
    
    def start_requests(self):
        """Start by scraping links inside #content_div_11796_11796."""
        start_url = "https://www.cardiff.ac.uk/about/organisation/college-structure"
        yield Request(
            url=start_url,
            callback=self.parse_initial_links,
            meta={"playwright": True, "playwright_include_page": True},
        )

    async def parse_initial_links(self, response):
        """Extract initial links and process them sequentially."""
        page = response.meta["playwright_page"]
        await page.wait_for_load_state("networkidle")
        
        # Extract links inside the target div
        links = await page.eval_on_selector_all(
            "#content_div_11796_11796 ul a", "elements => elements.map(e => e.href)"
        )
        await page.close()

        # Append "/people/academic-staff" to each extracted link
        full_urls = [f"{link}/people/academic-staff" for link in links]

        # Process the first URL and pass the remaining in meta
        if full_urls:
            first_url = full_urls[0]
            remaining_urls = full_urls[1:]
            yield Request(
                url=first_url,
                callback=self.parse_navigation_links,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "remaining_full_urls": remaining_urls,
                },
            )

    async def parse_navigation_links(self, response):
        """Process navigation links sequentially."""
        page = response.meta["playwright_page"]
        await page.wait_for_load_state("networkidle")

        # Extract navigation links
        nav_links = await page.eval_on_selector_all(
            ".nav-item.nav-local-section.nav-local-section-open ul a", 
            "elements => elements.map(e => e.href)"
        )
        await page.close()

        remaining_full_urls = response.meta.get("remaining_full_urls", [])

        if nav_links:
            # Process the first nav link and pass the remaining in meta
            first_nav_link = nav_links[0]
            remaining_nav_links = nav_links[1:]
            yield Request(
                url=first_nav_link,
                callback=self.extract_emails,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "remaining_nav_links": remaining_nav_links,
                    "remaining_full_urls": remaining_full_urls,
                },
            )
        else:
            # No nav links, directly extract emails from current URL
            yield Request(
            url=response.url,
            callback=self.extract_emails,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "remaining_full_urls": remaining_full_urls,
            },
            dont_filter=True,  # This prevents the duplicate filter from dropping this request.
        )

    async def extract_emails(self, response):
        page = response.meta["playwright_page"]
        regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

        try:
            await page.wait_for_load_state("networkidle")
            content = await page.content()
            current_emails = set(regex.findall(content))

            new_emails = current_emails - self.seen_emails
            for email in new_emails:
                self.seen_emails.add(email)
                yield {"email": email, "university": "cardiff.ac.uk"}

        except Exception as e:
            logger.error(f"Error extracting emails from {response.url}: {e}")

        finally:
            logger.info(f"Closing page for {response.url}")
            await page.close()

        # Retrieve remaining links from meta
        remaining_nav_links = response.meta.get("remaining_nav_links", [])
        remaining_full_urls = response.meta.get("remaining_full_urls", [])

        # Continue with nav links if available
        if remaining_nav_links:
            next_nav_link = remaining_nav_links[0]
            remaining_nav = remaining_nav_links[1:]
            yield Request(
                url=next_nav_link,
                callback=self.extract_emails,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "remaining_nav_links": remaining_nav,
                    "remaining_full_urls": remaining_full_urls,
                },
            )
        # Otherwise, if there are remaining full URLs, proceed with them
        elif remaining_full_urls:
            next_full_url = remaining_full_urls[0]
            remaining_full = remaining_full_urls[1:]
            yield Request(
                url=next_full_url,
                callback=self.parse_navigation_links,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "remaining_full_urls": remaining_full,
                },
            )

