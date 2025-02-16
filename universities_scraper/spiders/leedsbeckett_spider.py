import scrapy
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import re
class LeedsBeckettSpider(scrapy.Spider):
    name = "leedsbeckett_spider"
    
    
    def __init__(self, name = None, **kwargs):
        self.base_url = "https://www.leedsbeckett.ac.uk/search"
        super().__init__(name, **kwargs)
    
    def start_requests(self):
        """Start with the first URL and pass along the rest in meta."""
        urls = [
            "https://www.leedsbeckett.ac.uk/search/?area=people&f.Department%7CpeopleDepartment=Leeds+School+Of+Arts&form=partial&collection=leedsbeckett-meta&f.Filters%7Cleedsbeckett-academic-staff=People",
            "https://www.leedsbeckett.ac.uk/search/?f.Department%7CpeopleDepartment=Leeds+Business+School&form=partial&collection=leedsbeckett-meta&f.Filters%7Cleedsbeckett-academic-staff=People",
            "https://www.leedsbeckett.ac.uk/search/?f.Department%7CpeopleDepartment=Leeds+Business+School&form=partial&collection=leedsbeckett-meta&f.Filters%7Cleedsbeckett-academic-staff=People",
            "https://www.leedsbeckett.ac.uk/search/?f.Department%7CpeopleDepartment=Carnegie+School+Of+Education&form=partial&collection=leedsbeckett-meta&f.Filters%7Cleedsbeckett-academic-staff=People",
            "https://www.leedsbeckett.ac.uk/search/?f.Department%7CpeopleDepartment=School+Of+Events%2C+Tourism+And+Hospitality+Management&form=partial&collection=leedsbeckett-meta&f.Filters%7Cleedsbeckett-academic-staff=People",
            "https://www.leedsbeckett.ac.uk/search/?f.Department%7CpeopleDepartment=School+Of+Health&form=partial&collection=leedsbeckett-meta&f.Filters%7Cleedsbeckett-academic-staff=People",
            "https://www.leedsbeckett.ac.uk/search/?f.Department%7CpeopleDepartment=School+Of+Health&form=partial&collection=leedsbeckett-meta&f.Filters%7Cleedsbeckett-academic-staff=People",
            "https://www.leedsbeckett.ac.uk/search/?f.Department%7CpeopleDepartment=School+of+Humanities+and+Social+Sciences&form=partial&collection=leedsbeckett-meta&f.Filters%7Cleedsbeckett-academic-staff=People",
            "https://www.leedsbeckett.ac.uk/search/?f.Department%7CpeopleDepartment=Leeds+Law+School&form=partial&collection=leedsbeckett-meta&f.Filters%7Cleedsbeckett-academic-staff=People",
            "https://www.leedsbeckett.ac.uk/search/?f.Department%7CpeopleDepartment=Carnegie+School+Of+Sport&form=partial&collection=leedsbeckett-meta&f.Filters%7Cleedsbeckett-academic-staff=People",
        ]
        # Start with the first URL and pass the remaining URLs in meta.
        first_url = urls[0]
        remaining_urls = urls[1:]
        
        yield Request(
            url=first_url,
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "remaining_urls": remaining_urls,
            },
        )
        
    async def parse(self, response):
        page = response.meta["playwright_page"]
        regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
        try:
            # Extract profile links
            while True:
                await page.wait_for_load_state("networkidle")
                html = await page.content()
                soup = BeautifulSoup(html, "lxml")
                emails = set(regex.findall(soup.get_text()))
                for email in emails:
                    yield {"email": email, "university": "leedsbeckett.ac.uk"}
                
                # Click the next button if available
                button = soup.find("a", attrs={"aria-label": "show next page"})
                if button:
                    href = button.get("href")
                    next_url = urljoin(self.base_url, href)
                    await page.goto(next_url)
                else:
                    break
                
                
        except PlaywrightTimeoutError:
            self.logger.error("Timeout error occurred while scraping.")
        
        finally:
            await page.close()
              
            # Retrieve the remaining URLs from meta and, if available, schedule the next request.
            remaining_urls = response.meta.get("remaining_urls", [])
            if remaining_urls:
                next_url = remaining_urls[0]
                remaining_urls = remaining_urls[1:]
                yield Request(
                    url=next_url,
                    callback=self.parse,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "remaining_urls": remaining_urls,
                    },
                )

        
