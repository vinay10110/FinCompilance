import requests
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure retry strategy
retry_strategy = Retry(
    total=3,  # number of retries
    backoff_factor=1,  # wait 1, 2, 4 seconds between retries
    status_forcelist=[500, 502, 503, 504]  # HTTP status codes to retry on
)
http = requests.Session()
http.mount("https://", HTTPAdapter(max_retries=retry_strategy))
http.mount("http://", HTTPAdapter(max_retries=retry_strategy))

# Constants
base_url = "https://rbi.org.in/Scripts/"
page_url = "https://rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx"
storage_file = "rbi_press_releases.json"

# Load existing data (if any)
if os.path.exists(storage_file):
    with open(storage_file, "r") as f:
        known_links = {item["press_release_link"] for item in json.load(f)}
else:
    known_links = set()

def scrape_rbi():
    response = http.get(page_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.find_all("tr")

    new_data = []
    for row in rows:
        link_tag = row.find("a", class_="link2")
        if not link_tag:
            continue

        title = link_tag.text.strip()
        relative_link = link_tag["href"]
        full_link = base_url + relative_link

        # Skip if we've already scraped this link
        if full_link in known_links:
            continue

        pdf_tag = row.find("a", target="_blank")
        pdf_url = pdf_tag["href"] if pdf_tag else None

        # Get date if available (you might need to adjust this based on the actual HTML structure)
        date_cell = row.find("td", class_="date")  # Adjust class name as needed
        date_published = date_cell.text.strip() if date_cell else datetime.now().strftime("%Y-%m-%d")

        entry = {
            "title": title,
            "press_release_link": full_link,
            "pdf_link": pdf_url,
            "date_published": date_published,
            "is_new": True,
            "doc_id": f"doc_{hash(full_link)}",  # Generate a unique doc_id
            "date_scraped": datetime.now().strftime("%Y-%m-%d")
        }

        new_data.append(entry)
        known_links.add(full_link)

    return new_data

def save_to_local(data):
    if os.path.exists(storage_file):
        with open(storage_file, "r") as f:
            existing = json.load(f)
    else:
        existing = []

    # Mark older entries as not new
    for entry in existing:
        entry['is_new'] = False

    updated = data + existing  # Put new entries at the start

    with open(storage_file, "w") as f:
        json.dump(updated, f, indent=4)

def get_document_url(doc_id: str) -> str:
    """Get the PDF URL for a document ID.
    
    Args:
        doc_id: The document ID to look up
        
    Returns:
        str: The PDF URL if found, None otherwise
    """
    try:
        if not os.path.exists(storage_file):
            return None
            
        with open(storage_file, "r") as f:
            documents = json.load(f)
            
        for doc in documents:
            if doc.get('doc_id') == doc_id:
                return doc.get('pdf_link')
                
        return None
    except Exception as e:
        print(f"Error getting document URL: {str(e)}")
        return None

# Only run the continuous loop if this file is run directly
if __name__ == "__main__":
    print("🔁 Starting continuous RBI scraper...")

    try:
        while True:
            print("🔍 Checking for new press releases...")
            new_entries = scrape_rbi()
            if new_entries:
                print(f"✅ Found {len(new_entries)} new press release(s). Saving...")
                save_to_local(new_entries)
                for entry in new_entries:
                    print(f"\nTitle: {entry['title']}")
                    print(f"Press Release Link: {entry['press_release_link']}")
                    print(f"PDF Link: {entry['pdf_link']}")
            else:
                print("⏳ No new press releases found.")

            # Wait 10 minutes before next check
            time.sleep(600)

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")