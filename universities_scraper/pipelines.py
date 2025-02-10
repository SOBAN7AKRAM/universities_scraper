import csv
import os

class UniversitiesScraperPipeline:
    def open_spider(self, spider):
        # Create the folder to hold CSV files if it doesn't exist.
        os.makedirs("emails", exist_ok=True)
        # Dictionary to store open file handles and writers keyed by university id.
        self.university_files = {}

    def process_item(self, item, spider):
        university = item.get("university", "default")
        email = item["email"]

        # If this university doesn't have a file opened yet, open it.
        if university not in self.university_files:
            filename = os.path.join("emails", f"{university}_emails.csv")
            f = open(filename, "w", newline="", encoding="utf-8")
            writer = csv.writer(f)
            # Write header if the file is empty.
            if os.stat(filename).st_size == 0:
                writer.writerow(["Email"])
            self.university_files[university] = {
                "file": f,
                "writer": writer,
                "emails_seen": set()
            }
        
        # Check for duplicates per university and write the email if it's new.
        university_data = self.university_files[university]
        if email not in university_data["emails_seen"]:
            university_data["emails_seen"].add(email)
            university_data["writer"].writerow([email])
            university_data["file"].flush()  # Flush to see data immediately.
        
        return item

    def close_spider(self, spider):
        # Close all open file handles.
        for data in self.university_files.values():
            data["file"].close()
