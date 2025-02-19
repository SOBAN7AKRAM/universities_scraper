import scrapy
import re
from bs4 import BeautifulSoup
from scrapy import Request

class RoehamptonSpider(scrapy.Spider):
    name = "roehampton_spider"
    base_url = "https://www.roehampton.ac.uk/general-information/find-staff/"
    
    def start_requests(self):
        # Start with the letter A.
        initial_letter = "A"
        yield Request(
            url=self.base_url,
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_context": "university-scraper",
                "letter": initial_letter,
            },
        )
    
    async def parse(self, response):
        page = response.meta["playwright_page"]
        # Get the starting letter; default to "A" if not present.
        letter = response.meta.get("letter", "A")
        # Regex to find email addresses.
        regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
        
        try:
            # Loop through letters from the current one to Z.
            while letter <= "Z":
                # Wait for the search input field to be available.
                await page.wait_for_selector("input#lastname")
                # Fill the input with the current letter (Playwright's fill() clears existing text).
                await page.fill("input#lastname", letter)
                
                # Wait for and click the search button.
                await page.wait_for_selector("button#namesubmit")
                await page.click("button#namesubmit")
                
                # Wait for the dynamic content to load.
                await page.wait_for_timeout(4000)
                
                # Get the updated page content.
                content = await page.content()
                soup = BeautifulSoup(content, "lxml")
                
                # Extract email addresses from the page text.
                emails = set(re.findall(regex, soup.get_text()))
                for email in emails:
                    yield {"email": email, "university": "roehampton.ac"}
                
                self.logger.info(f"Processed letter {letter}: found {len(emails)} emails.")
                
                # Move to the next letter.
                letter = chr(ord(letter) + 1)
                
        except Exception as e:
            self.logger.error(f"Error processing letter {letter}: {e}")
        finally:
            await page.close()
