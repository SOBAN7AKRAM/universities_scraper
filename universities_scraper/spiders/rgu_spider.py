import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

class RguSpider(scrapy.Spider):
    name = "rgu_spider"
    
    def start_requests(self):
        url = "https://www.rgu.ac.uk/contact-us/staff-directory"
            
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
            # Wait for the select element with id "school-list"
            select_elem = await page.wait_for_selector("#school-list", state="visible", timeout=5000)

            # Query all <option> elements inside the select element
            option_elements = await select_elem.query_selector_all("option")

            # Loop over each option element
            for option in option_elements:
                # Get the value attribute of the option
                option_value = await option.get_attribute("value")

                # Select the option by its value
                await select_elem.select_option(option_value)

                await page.wait_for_timeout(2000)  # Wait 1 second before continuing
                content = await page.content()
                emails = set(regex.findall(content))
                for email in emails:
                    yield {"email": email, "university": "rgu.ac.uk"}


        finally:
            await page.close()