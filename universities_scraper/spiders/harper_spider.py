import scrapy
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import os
from urllib.parse import urljoin

class HarperSpider(scrapy.Spider):
    name = "harper_spider"
    
    def __init__(self, *args, **kwargs):
        self.start_url = "https://www.harper-adams.ac.uk/general/staff/"
        self.output_folder = "urls"
        self.html_filename = "harper_links.txt"
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Clear (or create) the file at start-up
        with open(os.path.join(self.output_folder, self.html_filename), "w", encoding="utf-8") as f:
            f.write("")
            
        super().__init__(*args, **kwargs)
    
    def start_requests(self):
        yield Request(
            url=self.start_url,
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_context": "university-scraper",
            },
        )
        
    async def parse(self, response):
        page = response.meta["playwright_page"]
        existing_links = set()
        try:
            select_element = await page.query_selector("#sel_department")
            option_values = await select_element.eval_on_selector_all(
                "option", "options => options.map(action => action.value)" 
            )
            
            for val in option_values:
                if val == 0:
                    continue
                await page.select_option("#sel_department", value=val)
                
                await page.wait_for_load_state("networkidle")
                # profile_links = 

        except PlaywrightTimeoutError:
            self.logger.error("Timeout error occurred while scraping.")
        
        finally:
            await page.close()
