from itemadapter import ItemAdapter
import csv
import os

class UniversitiesScraperPipeline:
    def open_spider(self, spider):
        # Use spider name in filename to avoid conflicts
        os.makedirs("emails", exist_ok=True)
        self.filename = os.path.join("emails", f"{spider.name}_emails.csv")
        # self.filename = f"{spider.name}_emails.csv"
        # Write header only if file doesn't exist
        self.file = open(self.filename, "a", newline="", encoding="utf-8")
        self.writer = csv.writer(self.file)
        if os.stat(self.filename).st_size == 0:
            self.writer.writerow(["Email"])
        
        self.emails_seen = set()
        # Load existing emails if resuming
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                self.emails_seen = {row[0].lower() for row in reader}

    def process_item(self, item, spider):
        email = item["email"]
        if email not in self.emails_seen:
            self.emails_seen.add(email)
            self.writer.writerow([email])
            self.file.flush()  # Ensure immediate write to disk
        return item

    def close_spider(self, spider):
        self.file.close()