import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List, Dict, Any
import dateutil.parser
import pytz

logger = logging.getLogger(__name__)

class RBIWebScraper:
    def __init__(self):
        self.base_url = "https://rbi.org.in/Scripts/"
        self.page_url = "https://rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx"
        self.logger = logging.getLogger(__name__)
        self.previous_updates = []  # Store previous updates in memory
        
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string into datetime object"""
        try:
            # Parse date with dateutil and set timezone to IST
            date = dateutil.parser.parse(date_str)
            ist = pytz.timezone('Asia/Kolkata')
            return date.astimezone(ist)
        except Exception as e:
            self.logger.error(f"Error parsing date {date_str}: {e}")
            return None

    def scrape(self) -> Dict[str, Any]:
        """Scrape RBI website for updates and compare with previous scrape"""
        try:
            self.logger.info("Starting RBI website scraping")
            response = requests.get(self.page_url)
            response.raise_for_status()

            if not response.content:
                self.logger.error("Empty response from RBI website")
                return {"all_updates": [], "new_updates": []}

            soup = BeautifulSoup(response.content, "html.parser")
            rows = soup.find_all("tr")
            
            current_updates = []
            
            for row in rows:
                try:
                    link_tag = row.find("a", class_="link2")
                    if not link_tag:
                        continue

                    title = link_tag.text.strip()
                    relative_link = link_tag.get("href")
                    
                    if not relative_link:
                        self.logger.warning(f"No href found for title: {title}")
                        continue
                        
                    full_link = self.base_url + relative_link

                    pdf_tag = row.find("a", target="_blank")
                    pdf_url = pdf_tag.get("href") if pdf_tag else None

                    date_cell = row.find("td", width="15%")
                    date_str = date_cell.text.strip() if date_cell else None
                    date_published = self._parse_date(date_str) if date_str else None

                    update = {
                        "title": title,
                        "press_release_link": full_link,
                        "pdf_link": pdf_url,
                        "date_published": date_published.isoformat() if date_published else None,
                        "date_scraped": datetime.utcnow().isoformat(),
                        "is_new": False
                    }
                    
                    current_updates.append(update)

                except Exception as row_error:
                    self.logger.error(f"Error processing row: {str(row_error)}")
                    continue

            # Find new updates by comparing with previous scrape
            new_updates = []
            if self.previous_updates:
                previous_links = {u["press_release_link"] for u in self.previous_updates}
                new_updates = [
                    {**update, "is_new": True}
                    for update in current_updates
                    if update["press_release_link"] not in previous_links
                ]
            
            # Store current updates for future comparison
            self.previous_updates = current_updates
            
            return {
                "all_updates": current_updates,
                "new_updates": new_updates
            }

        except requests.RequestException as req_error:
            self.logger.error(f"Request error while scraping RBI website: {str(req_error)}")
            return {"all_updates": [], "new_updates": []}
        except Exception as e:
            self.logger.error(f"Unexpected error while scraping RBI website: {str(e)}")
            return {"all_updates": [], "new_updates": []}