import scrapy
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import os
import re
import csv

logger = logging.getLogger(__name__)

class ImperialSpider(scrapy.Spider):
    name = "imperial_spider"
    
    def __init__(self, *args, **kwargs):
        # Starting URL for crawling
        self.start_url = "https://www.imperial.ac.uk/school-public-health/infectious-disease-epidemiology/contact-us/all-staff-a-z/"
        # Folder and filename where email elements HTML will be stored
        self.output_folder = "output"
        self.html_filename = "imperial.html"
        os.makedirs(self.output_folder, exist_ok=True)
        # Clear (or create) the file at start-up
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")
        super().__init__(*args, **kwargs)
    
    def start_requests(self):
        yield Request(
            url=self.start_url,
            callback=self.extract_emails,
            meta={
                "playwright": True,
                "playwright_include_page": True,
            },
        )
    
    async def extract_emails(self, response):
        page = response.meta["playwright_page"]
        try:
            # Wait for the page to finish loading
            await page.wait_for_load_state('networkidle')
            
            # Extract the entire HTML of the page.
            page_html = await page.content()
            file_path = os.path.join(self.output_folder, self.html_filename)
            # Append the page HTML (with a separator) to the file.
            with open(file_path, "a", encoding="utf-8") as f:
                f.write("\n<!-- PAGE SEPARATOR -->\n")
                f.write(page_html)
            
            # Look for the pagination next-page element.
            next_page_element = await page.query_selector('.next-page')
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
    
    def closed(self, reason):
        """
        After all pages have been crawled, read the aggregated HTML file,
        use BeautifulSoup to extract emails, and log (or further process) them.
        """
        file_path = os.path.join(self.output_folder, self.html_filename)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            soup = BeautifulSoup(html_content, "html.parser")
            # Find all <a> tags with an href attribute (assumed to be the email links)
            os.makedirs("emails", exist_ok=True)
            csv_file = os.path.join("emails", "imperial.ac.uk_emails.csv")

            # (Optional) If you want to write a header row only once, you can check if the file exists.
            if not os.path.exists(csv_file):
                with open(csv_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["email"])  # Write header

            # Assume that soup is already created from your aggregated HTML:
            # For example: soup = BeautifulSoup(aggregated_html, "html.parser")
            email_links = soup.find_all("a", href=True)
            with open(csv_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for link in email_links:
                    href = link["href"]
                    # Only process mailto links.
                    if href.startswith("mailto:"):
                        # Remove the "mailto:" prefix and strip any surrounding whitespace.
                        email = re.sub(r'^mailto:', '', href).strip()
                        logger.info(f"Extracted email: {email}")
                        # Write the email as a new row in the CSV file.
                        writer.writerow([email])