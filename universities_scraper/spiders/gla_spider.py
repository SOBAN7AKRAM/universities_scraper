import scrapy
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from scrapy import Request

class GlaSpider(scrapy.Spider):
    name = "gla_spider"
    base_url = "https://www.gla.ac.uk/stafflist/"
    output_folder = "urls"
    html_filename = "gla.txt"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        os.makedirs(self.output_folder, exist_ok=True)
        # Clear (or create) the output file at start-up.
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")

    def start_requests(self):
        # Load the main staff list page to extract school dropdown options.
        yield Request(
            url=self.base_url,
            callback=self.parse_schools,
            meta={"playwright": True, "playwright_include_page": True},
        )

    async def parse_schools(self, response):
        page = response.meta["playwright_page"]
        try:
            content = await page.content()
            soup = BeautifulSoup(content, "lxml")
            select_element = soup.select_one("#select_id_schools")
            if not select_element:
                self.logger.error("Dropdown not found")
                return

            # Loop over each <option> and skip the default empty value.
            for option in select_element.find_all("option"):
                school_value = option.get("value", "").strip()
                if not school_value:
                    continue  # Skip the default option

                school_name = option.get_text(strip=True)
                self.logger.info(f"Processing school: {school_name} (value: {school_value})")

                # Re-open the base page and simulate the form interaction.
                yield Request(
                    url=self.base_url,
                    callback=self.parse_school,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "school_value": school_value,
                        "school_name": school_name,
                    },
                    dont_filter=True,
                )
        finally:
            await page.close()

    async def parse_school(self, response):
        """
        1. Wait for the dropdown.
        2. Select the school.
        3. Wait briefly.
        4. Trigger a JavaScript click on the second submit button.
        5. Wait for navigation and then extract data.
        """
        page = response.meta["playwright_page"]
        school_value = response.meta["school_value"]
        school_name = response.meta["school_name"]

        try:
            # Ensure the dropdown is available.
            await page.wait_for_selector("#select_id_schools")
            
            # Select the school option.
            await page.select_option("#select_id_schools", value=school_value)
            
            # Wait a moment to let any onchange events settle.
            await page.wait_for_timeout(500)
            
            # Trigger the click on the second button using JavaScript.
            await page.evaluate("""() => {
                const buttons = document.querySelectorAll('button[type="submit"]');
                if (buttons.length >= 2) {
                    buttons[1].click();
                }
            }""")
            
            # Wait for navigation or AJAX content update.
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(1000)  # additional wait if necessary
            
            # Extract the page content.
            content = await page.content()
            soup = BeautifulSoup(content, "lxml")
            new_links = set()

            # Update the selector as needed to capture the desired links.
            for element in soup.select("a.maincontent"):
                href = element.get("href")
                if href:
                    new_links.add(urljoin(self.base_url, href))
            
            if new_links:
                with open(os.path.join(self.output_folder, self.html_filename), "a", encoding="utf-8") as f:
                    for href in new_links:
                        f.write(f"{href}\n")
                self.logger.info(f"Extracted {len(new_links)} links for school: {school_name}")
            else:
                self.logger.info(f"No links found for school: {school_name}")
                
        except Exception as e:
            self.logger.error(f"Error processing school {school_name}: {e}")
        finally:
            await page.close()
