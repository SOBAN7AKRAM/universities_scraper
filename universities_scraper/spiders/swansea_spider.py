import scrapy
import re
from scrapy import Request
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import logging
from bs4 import BeautifulSoup
logger = logging.getLogger(__name__)

class SwanseaSpider(scrapy.Spider):
    name = "swansea_spider"
    
    def start_requests(self):
        """Start with the first URL and pass along the rest in meta."""
        urls = [
            "https://www.swansea.ac.uk/staff/humanities-and-socialsciences/culture-communication-staff/american-studies-staff/",
            "https://www.swansea.ac.uk/staff/humanities-and-socialsciences/culture-communication-staff/classics-ancient-history-egyptology-staff/",
            "https://www.swansea.ac.uk/staff/humanities-and-socialsciences/culture-communication-staff/english-language-tesol-applied-linguistics-staff/",
            "https://www.swansea.ac.uk/staff/humanities-and-socialsciences/culture-communication-staff/english-language-creative-writing-staff/",
            "https://www.swansea.ac.uk/staff/humanities-and-socialsciences/culture-communication-staff/history-staff/",
            "https://www.swansea.ac.uk/staff/humanities-and-socialsciences/culture-communication-staff/media-communication-journalism-pr-staff/",
            "https://www.swansea.ac.uk/staff/humanities-and-socialsciences/culture-communication-staff/modern-languages-translation-interpreting-staff/",
            "https://www.swansea.ac.uk/staff/humanities-and-socialsciences/culture-communication-staff/welsh-staff/",
            "https://www.swansea.ac.uk/staff/humanities-and-socialsciences/management-staff/accounting-finance-staff/",
            "https://www.swansea.ac.uk/staff/humanities-and-socialsciences/management-staff/business-management-staff/",
            "https://www.swansea.ac.uk/staff/humanities-and-socialsciences/law-staff/",
            "https://www.swansea.ac.uk/staff/humanities-and-socialsciences/social-sciences-staff/criminology-sociology-social-policy-staff/",
            "https://www.swansea.ac.uk/staff/humanities-and-socialsciences/social-sciences-staff/economics-staff/",
            "https://www.swansea.ac.uk/staff/humanities-and-socialsciences/social-sciences-staff/education-childhood-studies-staff/",
            "https://www.swansea.ac.uk/staff/humanities-and-socialsciences/social-sciences-staff/politics-philosophy-international-relations-staff/",
            "https://www.swansea.ac.uk/staff/medicine-health-life-science/health-social-care/ethics-law/",
            "https://www.swansea.ac.uk/staff/medicine-health-life-science/health-social-care/healthcare-science/",
            "https://www.swansea.ac.uk/staff/medicine-health-life-science/health-social-care/midwifery/",
            "https://www.swansea.ac.uk/staff/medicine-health-life-science/health-social-care/nursing/",
            "https://www.swansea.ac.uk/staff/medicine-health-life-science/psychology/",
            "https://www.swansea.ac.uk/staff/medicine-health-life-science/medicine/biomedical-sciences/",
            "https://www.swansea.ac.uk/staff/medicine-health-life-science/medicine/health-data-science/",
            "https://www.swansea.ac.uk/staff/medicine-health-life-science/medicine/pharmacy/",
            "https://www.swansea.ac.uk/staff/medicine-health-life-science/centre-for-innovative-ageing/",
            "https://www.swansea.ac.uk/staff/science-and-engineering/honorary-and-emeritus-staff/",
            "https://www.swansea.ac.uk/staff/science-and-engineering/school-of-aerospace-civil-electrical-and-mechanical-engineering-staff/aerospace/",
            "https://www.swansea.ac.uk/staff/science-and-engineering/school-of-aerospace-civil-electrical-and-mechanical-engineering-staff/civil/",
            "https://www.swansea.ac.uk/staff/science-and-engineering/school-of-aerospace-civil-electrical-and-mechanical-engineering-staff/mechanical/",
            "https://www.swansea.ac.uk/staff/science-and-engineering/school-of-aerospace-civil-electrical-and-mechanical-engineering-staff/electrical/",
            "https://www.swansea.ac.uk/staff/science-and-engineering/school-of-biosciences-geography-and-physics-staff/physics/",
            "https://www.swansea.ac.uk/staff/science-and-engineering/school-of-biosciences-geography-and-physics-staff/biosciences/",
            "https://www.swansea.ac.uk/staff/science-and-engineering/school-of-biosciences-geography-and-physics-staff/geography/",
            "https://www.swansea.ac.uk/staff/science-and-engineering/school-of-mathematics-and-computer-science-staff/compsci/",
            "https://www.swansea.ac.uk/staff/science-and-engineering/school-of-mathematics-and-computer-science-staff/maths/",
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
        regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

        try:
            await page.wait_for_load_state("networkidle")
            html = await page.content()
            soup = BeautifulSoup(html, "lxml")
            current_emails = set(regex.findall(soup.get_text()))
            for email in current_emails:
                yield {"email": email, "university": "swansea.ac.uk"}

        except Exception as e:
            logger.error(f"Error processing {response.url}: {e}")

        finally:
            await page.close()

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
