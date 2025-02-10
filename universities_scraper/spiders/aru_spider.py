import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

class AruSpider(scrapy.Spider):
    name = "aru_spider"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # List to hold all collected profile URLs
        self.all_profile_links = []

    def start_requests(self):
        urls = [
            "https://www.aru.ac.uk/arts-humanities-education-and-social-sciences/faculty-staff"
        ]
        for url in urls:
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
        
        try:
            # Handle cookie consent
            try:
                cookie_accept = await page.wait_for_selector(
                    "button.sc-dcJsrY.ffwiLo",
                    state="visible",
                    timeout=5000
                )
                await cookie_accept.click()
                self.logger.info("Clicked cookie consent")
                await page.wait_for_timeout(1000)
            except PlaywrightTimeoutError:
                self.logger.info("No cookie consent found")
            
            # Loop through pagination until no more "Next" pages.
            while True:
                # Extract all staff profile links on the current page.
                profile_links = await page.query_selector_all(".staff-listing__details a")
                if not profile_links:
                    self.logger.warning("No profile links found on this page.")
                else:
                    for link in profile_links:
                        profile_url = await link.get_attribute("href")
                        if profile_url:
                            full_url = response.urljoin(profile_url)
                            # Avoid duplicates.
                            if full_url not in self.all_profile_links:
                                self.all_profile_links.append(full_url)
                                self.logger.info("Collected profile URL: %s", full_url)
                
                # Try to click the "Next" pagination button.
                try:
                    next_button = await page.wait_for_selector(
                        "span.visually-hidden-sm:has-text('Next')",
                        state="visible",
                        timeout=5000
                    )
                    await next_button.scroll_into_view_if_needed()
                    await next_button.click()
                    
                    # Wait for new content to load.
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(5000)
                except PlaywrightTimeoutError:
                    self.logger.info("No more pagination pages or button disabled.")
                    break
                except Exception as e:
                    self.logger.error("Error during pagination: %s", str(e))
                    break
        finally:
            await page.close()
        
        # After finishing pagination, yield a new Request for each collected profile URL.
        self.logger.info("Total profile URLs collected: %d", len(self.all_profile_links))
        for profile_url in self.all_profile_links:
            yield Request(
                url=profile_url,
                callback=self.parse_profile,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_context": "university-scraper",
                },
            )
    
    async def parse_profile(self, response):
        page = response.meta["playwright_page"]
        await page.wait_for_load_state("networkidle")
        content = await page.content()
        
        # Use regex to extract emails from the profile page.
        regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
        emails = set(regex.findall(content))
        for email in emails:
            yield {"email": email, "university": "aru.ac.uk"}
        await page.close()
