import scrapy
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

class QmuSpider(scrapy.Spider):
    name = "qmu_spider"
    
    def start_requests(self):
        """Start with the first URL and pass along the rest in meta."""
        urls = [
            "https://www.qmu.ac.uk/schools-and-divisions/dnbsppr/radiography/radio-staff",
            "https://www.qmu.ac.uk/schools-and-divisions/shs/shs-staff",
            "https://www.qmu.ac.uk/schools-and-divisions/ighd/ighd-staff",
            "https://www.qmu.ac.uk/schools-and-divisions/dnbsppr/dnbs/dnbs-staff",
            "https://www.qmu.ac.uk/schools-and-divisions/nursing/nursing-and-paramedic-staff",
            "https://www.qmu.ac.uk/schools-and-divisions/otat/otat-staff",
            "https://www.qmu.ac.uk/schools-and-divisions/dnbsppr/physiotherapy/physio-staff",
            "https://www.qmu.ac.uk/schools-and-divisions/dnbsppr/podiatry/podiatry-staff",
            "https://www.qmu.ac.uk/schools-and-divisions/mcpa/mcpa-staff",
            "https://www.qmu.ac.uk/schools-and-divisions/psychology-sociology-and-education/psychology-sociology-and-education-staff",
            "https://www.qmu.ac.uk/schools-and-divisions/business-school/business-school-staff",
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
        try:
            html = await page.content()
            soup = BeautifulSoup(html, "lxml")
            elements = soup.select("a[href^='mailto:']")
            for element in elements:
                email = element.get("href")
                email = re.sub(r"mailto:", "", email)  # Remove 'mailto:' prefix

                yield {"email": email, "university": "qmu.ac.uk"}
                
                
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

        
