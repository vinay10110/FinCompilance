import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from neon_database import db
import hashlib
from notifications import notify_new_circulars

page_url = "https://rbi.org.in/Scripts/BS_ViewMasterCirculardetails.aspx"


def generate_doc_id(url: str) -> str:
    """Generate a stable unique doc_id using SHA256"""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


async def scrape_rbi_circulars():
    # Fetch already stored links from DB
    known_links = db.get_existing_circular_links()
    print(f"Found {len(known_links)} existing circular links in database")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        new_data = []

        try:
            await page.goto(page_url, wait_until="networkidle")

            # Categories we want to scrape
            expected_categories = [
                "Banker and Debt Manager to Government",
                "Banker to Banks",
                "Banker to Governments and Banks",
                "Co-operative Banking",
                "Commercial Banking",
                "Financial Inclusion and Development",
                "Financial Market",
                "Foreign Exchange Management",
                "Issuer of Currency",
                "Non-banking",
                "Payment and Settlement System",
                "Primary Dealers"
            ]

            # Collect sidebar links
            sidebar_links = []
            all_links = await page.query_selector_all("a")

            for link in all_links:
                try:
                    link_text = (await link.inner_text() or "").strip()
                    href = await link.get_attribute("href")

                    if not link_text or not href:
                        continue

                    for expected_cat in expected_categories:
                        if expected_cat.lower() == link_text.lower():
                            sidebar_links.append(link)
                            break

                        if (len(link_text) > 15 and
                            any(word.lower() in link_text.lower()
                                for word in expected_cat.split() if len(word) > 3) and
                            len([word for word in expected_cat.split() if word.lower() in link_text.lower()]) >= 2):
                            if link not in sidebar_links:
                                sidebar_links.append(link)
                            break
                except:
                    continue

            category_links = []
            for category_el in sidebar_links:
                try:
                    category_text = (await category_el.inner_text() or "").strip()
                    category_href = await category_el.get_attribute("href")

                    if not category_text or not category_href:
                        continue

                    skip_patterns = ["Home", "Notifications", "Master Circulars", "http", "mailto"]
                    if any(pattern.lower() in category_text.lower() for pattern in skip_patterns):
                        continue

                    category_links.append({
                        "name": category_text,
                        "href": category_href
                    })
                except:
                    continue

            # Process each category
            for cat_data in category_links:
                try:
                    category = cat_data["name"]
                    cat_url = "https://rbi.org.in/Scripts/" + cat_data["href"]

                    await page.goto(cat_url, wait_until="networkidle")
                    await page.wait_for_timeout(2000)

                    main_content = await page.query_selector("table[width='100%']") or await page.query_selector("table")
                    if not main_content:
                        continue

                    rows = await main_content.query_selector_all("tr")
                    current_date = None

                    for row in rows:
                        try:
                            cells = await row.query_selector_all("td")
                            if len(cells) < 1:
                                continue

                            first_cell_text = (await cells[0].inner_text() or "").strip()

                            # Detect date header
                            try:
                                parsed_date = datetime.strptime(first_cell_text, "%b %d, %Y")
                                current_date = parsed_date.strftime("%Y-%m-%d")
                                continue
                            except:
                                pass

                            # Extract title
                            title_links = await row.query_selector_all("a")
                            title_link, title_text = None, None

                            for link in title_links:
                                text = (await link.inner_text() or "").strip()
                                href = await link.get_attribute("href")

                                if not text or not href:
                                    continue
                                if len(text) < 10 or text.lower() in ['pdf', 'download', 'click here']:
                                    continue

                                title_link, title_text = href, text
                                break

                            if not title_link or not title_text:
                                continue

                            # Find PDF link
                            pdf_link = None
                            pdf_elements = await row.query_selector_all(
                                "a[href*='.pdf'], img[src*='pdf'], a[href*='GetNotification']"
                            )

                            for element in pdf_elements:
                                try:
                                    tag_name = await element.evaluate("el => el.tagName")
                                    if tag_name.lower() == 'img':
                                        parent_link = await element.query_selector("xpath=..")
                                        if parent_link:
                                            pdf_href = await parent_link.get_attribute("href")
                                        else:
                                            continue
                                    else:
                                        pdf_href = await element.get_attribute("href")

                                    if pdf_href and ('.pdf' in pdf_href.lower() or 'GetNotification' in pdf_href):
                                        pdf_link = pdf_href
                                        break
                                except:
                                    continue

                            if not pdf_link:
                                # fallback search
                                for link in title_links:
                                    href = await link.get_attribute("href")
                                    if href and href != title_link:
                                        if '.pdf' in href.lower() or 'GetNotification' in href or 'download' in href.lower():
                                            pdf_link = href
                                            break

                            if not pdf_link:
                                continue

                            # Normalize link
                            if pdf_link.startswith("/"):
                                full_pdf_link = "https://rbi.org.in" + pdf_link
                            elif not pdf_link.startswith("http"):
                                full_pdf_link = "https://rbi.org.in/Scripts/" + pdf_link
                            else:
                                full_pdf_link = pdf_link

                            full_pdf_link = full_pdf_link.strip().lower()

                            if full_pdf_link in known_links:
                                continue

                            entry = {
                                "category": category,
                                "title": title_text,
                                "pdf_link": full_pdf_link,
                                "date_published": current_date or datetime.now().strftime("%Y-%m-%d"),
                                "is_new": True,
                                "doc_id": f"circular_{generate_doc_id(full_pdf_link)}",
                                "date_scraped": datetime.now().strftime("%Y-%m-%d"),
                            }

                            new_data.append(entry)

                        except:
                            continue
                except Exception as e:
                    print(f"Error processing category {category}: {e}")
                    continue

        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            await browser.close()

        if new_data:
            for entry in new_data:
                try:
                    db.save_circular(entry)
                except Exception as e:
                    print(f"Error saving circular to DB: {e}")
                    continue
            
            # Send Slack notification for new circulars
            try:
                notify_new_circulars(new_data)
            except Exception as e:
                print(f"Error sending Slack notification: {e}")

        print(f"Total new circulars found: {len(new_data)}")
        return new_data


async def scrape_and_save_circulars():
    try:
        new_entries = await scrape_rbi_circulars()
        print(f"Scraped {len(new_entries)} new circulars")
        return new_entries
    except Exception as e:
        print(f"Error in circular scraping: {e}")
        return []
