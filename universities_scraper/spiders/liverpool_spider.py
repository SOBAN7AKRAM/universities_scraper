import scrapy
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import logging
from urllib.parse import urljoin
import re
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)

class LiverpoolSpider(scrapy.Spider):
    name = "liverpool_spider"
    
    def __init__(self, *args, **kwargs):
        # Starting URL for crawling
        self.start_url = "https://www.liverpool.ac.uk/"
        super().__init__(*args, **kwargs)
    
    def start_requests(self):
        yield Request(
            url=urljoin(self.start_url, "/people/search?query=academic+staff&as_sfid=AAAAAAV-6n6Uwosoiv8cL0VNg_9scv4Tyoo--j2_Ne1CLRSPLOR4lFn0VeAuiUk3aPh03Ttph9gpplu5Fih9eAwCbA5B2PxcKlfutcm1BPXv_ixpg62dQtDxOyi1F9lM4aDMmIimfUFZFSVTFVk7587Wuf7F4iQK26ZX1vYnJ27Vt4bxDw%3D%3D&as_fid=1441acab49fd8570f91b24ab81193f9b9c57d8e3"),
            callback=self.extract_emails,
            meta={
                "playwright": True,
                "playwright_include_page": True,
            },
        )
    
    async def extract_emails(self, response):
        page = response.meta["playwright_page"]
        regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
        
        try:
            # extract emails
            content = await page.content()
            soup = BeautifulSoup(content, "lxml")
            emails = set(re.findall(regex, soup.get_text()))
            for email in emails:
                yield {"email": email, "university": "liverpool.ac.uk"}
            
            
            # Look for the pagination next-page element.
            next_page_element = soup.find('a', class_='next')
            if next_page_element:
                next_page_href = next_page_element.get("href")
                if next_page_href:
                    # Build the absolute URL by joining with the base URL.
                    next_page_url = urljoin(self.start_url, next_page_href)
                    logger.info(f"Navigating to next page: {next_page_url}")
                    yield Request(
                        url=next_page_url,
                        callback=self.extract_emails,
                        meta={
                            "playwright": True,
                            "playwright_include_page": True,
                        },
                    )
                else:
                    logger.info("Next page element found but no href attribute available.")
            else:
                logger.info("No next page link found.")
                
        except Exception as e:
            logger.error(f"Error processing {response.url}: {e}")
        finally:
            await page.close()