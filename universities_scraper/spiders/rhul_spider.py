import scrapy
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import logging
from urllib.parse import urljoin
import re
import random

logger = logging.getLogger(__name__)

class RhulSpider(scrapy.Spider):
    name = "rhul_spider"
    
    def __init__(self, *args, **kwargs):
        # Starting URL for crawling
        self.start_url = "https://pure.royalholloway.ac.uk/"
        super().__init__(*args, **kwargs)
    
    def start_requests(self):
        yield Request(
            url=urljoin(self.start_url, "en/persons/"),
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
            # Simulate random mouse movement to mimic human behavior.
            for _ in range(20):
                # Generate random coordinates (adjust max values as needed for your page)
                x = random.randint(0, 800)
                y = random.randint(0, 800)
                # Move the mouse gradually (using steps for a more human-like movement)
                await page.mouse.move(x, y, random.randint(1, 20))
                await page.wait_for_timeout(500)
            
            # Wait a little extra time before proceeding.
            # await page.wait_for_timeout(1000)
            await page.wait_for_load_state('networkidle')
            
            # --- CAPTCHA BYPASS ---
            # Look for the captcha element with id "px-captcha"
            captcha = await page.query_selector("#px-captcha")
            if captcha:
                bounding_box = await captcha.bounding_box()
                if bounding_box:
                    # Calculate the center of the captcha element.
                    cx = bounding_box["x"] + bounding_box["width"] / 2
                    cy = bounding_box["y"] + bounding_box["height"] / 2
                    logger.info("Captcha detected. Performing click-and-hold on captcha element.")
                    
                    # Move the mouse to the captcha element and click and hold.
                    await page.mouse.move(cx, cy, steps=10)
                    await page.mouse.down()
                    await page.wait_for_timeout(10000)  # Hold for 10 seconds
                    await page.mouse.up()
                    await page.wait_for_timeout(200)    # Additional small delay after releasing
                else:
                    logger.info("Captcha element found but no bounding box available.")
            else:
                logger.info("No captcha element detected.")
            # --- END CAPTCHA BYPASS ---
            
            # Extract emails from the page content.
            content = await page.content()
            emails = set(regex.findall(content))
            for email in emails:
                yield {"email": email, "university": "rhul.ac.uk"}
            
            # Look for the pagination next-page element.
            next_page_element = await page.query_selector('.nextLink')
            if next_page_element:
                next_page_href = await next_page_element.get_attribute("href")
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
