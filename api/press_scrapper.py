import requests
from datetime import datetime
from bs4 import BeautifulSoup
from neon_database import db
import hashlib
import re
from notifications import notify_new_press_releases
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

page_url = "https://rbi.org.in/Scripts/BS_PressreleaseDisplay.aspx"


def generate_doc_id(url: str) -> str:
    """Generate a stable unique doc_id using SHA256"""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def scrape_rbi():
    # Fetch already stored links from DB
    known_links = db.get_existing_links()
    
    # Setup session with retry strategy
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })

    response = session.get(page_url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    rows = soup.select("table tr")
    new_data = []
    current_date = None

    for row in rows:
        # Check if this row is a date header
        date_header = row.select_one("td.tableheader")
        if date_header:
            date_text = date_header.get_text().strip()

            # Parse the date header (e.g., "Aug 29, 2025")
            try:
                date_match = re.search(r'(\w{3} \d{1,2}, \d{4})', date_text)
                if date_match:
                    header_date = date_match.group(1)
                    parsed_date = datetime.strptime(header_date, "%b %d, %Y")
                    current_date = parsed_date.strftime("%Y-%m-%d")
            except Exception as e:
                print(f"Error parsing date header: {e}")
            continue

        # Process press release rows
        link_tag = row.select_one("a.link2")
        if not link_tag:
            continue

        title = link_tag.get_text().strip()
        relative_link = link_tag.get("href")

        if not relative_link:
            continue

        # Convert relative link to full URL for comparison
        if relative_link.startswith("http"):
            full_link = relative_link
        else:
            full_link = f"https://rbi.org.in/Scripts/{relative_link}"

        # Normalize link for comparison (strip and lowercase)
        normalized_link = full_link.strip().lower()
        
        # Debug: Check if this specific link exists
        is_duplicate = normalized_link in known_links
        
        if is_duplicate:
            continue  # Skip duplicates
        else:
            print(f"✅ NEW ENTRY: {title[:30]}...")

        pdf_tag = row.select_one("a[target='_blank']")
        pdf_url = pdf_tag.get("href") if pdf_tag else None

        # Use the current date from the header, or fallback to today
        date_published = current_date if current_date else datetime.now().strftime("%Y-%m-%d")

        entry = {
            "title": title,
            "press_release_link": normalized_link,  # Use normalized link for consistency
            "pdf_link": pdf_url,
            "date_published": date_published,
            "is_new": True,
            "doc_id": generate_doc_id(normalized_link),
            "date_scraped": datetime.now().strftime("%Y-%m-%d"),
        }

        new_data.append(entry)

    session.close()


    if new_data:
        for entry in new_data:
            try:
                db.save_press_release(entry)
            except Exception as e:
                print(f"Error saving press release to DB: {e}")
                pass
        
        # Send Slack notification for new press releases
        try:
            notify_new_press_releases(new_data)
        except Exception as e:
            print(f"Error sending Slack notification: {e}")
    else:
        print("No new press releases to save")

    return new_data


def scrape_and_save_press_releases():
    """Main function to scrape RBI press releases and save to database"""
    try:
        new_entries = scrape_rbi()
        print(f"Scraped {len(new_entries)} new press releases")
        return new_entries
    except Exception as e:
        print(f"Error in press release scraping: {e}")
        return []






