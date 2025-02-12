import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import logging
import os
from bs4 import BeautifulSoup
import csv

logger = logging.getLogger(__name__)

class NottinghamSpider(scrapy.Spider):
    name = "nottingham_spider"
    
    def __init__(self, *args, **kwargs):
        # Starting URL for crawling
        # Folder and filename where email elements HTML will be stored
        self.output_folder = "output"
        self.html_filename = "nottingham.html"
        os.makedirs(self.output_folder, exist_ok=True)
        # Clear (or create) the file at start-up
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")
        super().__init__(*args, **kwargs)
    
    def start_requests(self):
        """Start with the first URL and pass along the rest in meta."""
        urls = [
            "https://www.nottingham.ac.uk/clas/people/",
            "https://www.nottingham.ac.uk/CELE/people/staff.aspx",
            "https://www.nottingham.ac.uk/engineering/people/",
            "https://www.nottingham.ac.uk/humanities/departments/history/people/",
            "https://www.nottingham.ac.uk/english/people/",
            "https://www.nottingham.ac.uk/economics/people/",
            "https://www.nottingham.ac.uk/education/people/",
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

        try:
            await page.wait_for_load_state("networkidle")
            content = await page.content()
            file_path = os.path.join(self.output_folder, self.html_filename)
            # Append the page HTML (with a separator) to the file.
            with open(file_path, "a", encoding="utf-8") as f:
                f.write("\n<!-- PAGE SEPARATOR -->\n")
                f.write(content)

        except Exception as e:
            logger.error(f"Error processing {response.url}: {e}")


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
            csv_file = os.path.join("emails", "nottingham.ac.uk_emails.csv")

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
