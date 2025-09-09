import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from neon_database import db
import hashlib
import re

page_url = "https://rbi.org.in/Scripts/BS_PressreleaseDisplay.aspx"


def generate_doc_id(url: str) -> str:
    """Generate a stable unique doc_id using SHA256"""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


async def scrape_rbi():
    # Fetch already stored links from DB
    known_links = db.get_existing_links()
    print(f"Found {len(known_links)} existing links in database")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print(f"Navigating to {page_url}")
        await page.goto(page_url)

        rows = await page.query_selector_all("table tr")
        print(f"Found {len(rows)} table rows on the page")
        new_data = []
        current_date = None

        for row in rows:
            # Check if this row is a date header
            date_header = await row.query_selector("td.tableheader")
            if date_header:
                date_text = (await date_header.inner_text()).strip()

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
            link_tag = await row.query_selector("a.link2")
            if not link_tag:
                continue

            title = (await link_tag.inner_text()).strip()
            relative_link = await link_tag.get_attribute("href")

            # Convert relative link to full URL for comparison
            if relative_link.startswith("http"):
                full_link = relative_link
            else:
                full_link = f"https://rbi.org.in/Scripts/{relative_link}"

            # Normalize link
            full_link = full_link.strip().lower()

            print(f"Processing: {title[:50]}... | Link: {relative_link}")
            print(f"Full URL: {full_link}")

            if full_link in known_links:
                print(f"Skipping duplicate: {title[:30]}...")
                continue  # Skip duplicates

            pdf_tag = await row.query_selector("a[target='_blank']")
            pdf_url = await pdf_tag.get_attribute("href") if pdf_tag else None

            # Use the current date from the header, or fallback to today
            date_published = current_date if current_date else datetime.now().strftime("%Y-%m-%d")

            entry = {
                "title": title,
                "press_release_link": full_link,
                "pdf_link": pdf_url,
                "date_published": date_published,
                "is_new": True,
                "doc_id": generate_doc_id(full_link),
                "date_scraped": datetime.now().strftime("%Y-%m-%d"),
            }

            print(f"Adding new entry: {title[:30]}...")
            new_data.append(entry)

        await browser.close()

        print(f"Total new entries found: {len(new_data)}")

        # Save new data to database
        if new_data:
            for entry in new_data:
                try:
                    db.save_press_release(entry)
                except Exception as e:
                    print(f"Error saving press release to DB: {e}")
                    pass
        else:
            print("No new press releases to save")

        return new_data


async def scrape_and_save_press_releases():
    """Main function to scrape RBI press releases and save to database"""
    try:
        new_entries = await scrape_rbi()
        print(f"Scraped {len(new_entries)} new press releases")
        return new_entries
    except Exception as e:
        print(f"Error in press release scraping: {e}")
        return []


