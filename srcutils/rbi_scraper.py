import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..srcmodels.document_models import RBIUpdate, SessionLocal
import dateutil.parser
import pytz

logger = logging.getLogger(__name__)

class RBIWebScraper:
    def __init__(self):
        self.base_url = "https://rbi.org.in/Scripts/"
        self.page_url = "https://rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx"
        
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string into datetime object"""
        try:
            # Parse date with dateutil and set timezone to IST
            date = dateutil.parser.parse(date_str)
            ist = pytz.timezone('Asia/Kolkata')
            return date.astimezone(ist)
        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {e}")
            return None

    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape RBI website for new press releases"""
        try:
            response = requests.get(self.page_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            rows = soup.find_all("tr")

            db = SessionLocal()
            new_updates = []

            try:
                for row in rows:
                    link_tag = row.find("a", class_="link2")
                    if not link_tag:
                        continue

                    title = link_tag.text.strip()
                    relative_link = link_tag["href"]
                    full_link = self.base_url + relative_link

                    # Check if press release already exists
                    existing = db.query(RBIUpdate).filter_by(
                        press_release_link=full_link
                    ).first()
                    
                    if existing:
                        continue

                    pdf_tag = row.find("a", target="_blank")
                    pdf_url = pdf_tag["href"] if pdf_tag else None

                    # Extract date if available
                    date_cell = row.find("td", width="15%")
                    date_str = date_cell.text.strip() if date_cell else None
                    date_published = self._parse_date(date_str) if date_str else None

                    # Create new update record
                    update = RBIUpdate(
                        title=title,
                        press_release_link=full_link,
                        pdf_link=pdf_url,
                        date_published=date_published,
                        date_scraped=datetime.utcnow(),
                        is_new=True
                    )

                    db.add(update)
                    db.commit()
                    
                    new_updates.append({
                        "title": update.title,
                        "press_release_link": update.press_release_link,
                        "pdf_link": update.pdf_link,
                        "date_published": update.date_published.isoformat() if update.date_published else None,
                        "date_scraped": update.date_scraped.isoformat(),
                        "is_new": update.is_new
                    })

            finally:
                db.close()

            logger.info(f"Found {len(new_updates)} new press releases")
            return new_updates

        except Exception as e:
            logger.error(f"Error scraping RBI website: {e}")
            return []

    def get_updates(self, limit: int = 10, new_only: bool = False) -> List[Dict[str, Any]]:
        """Get updates from database"""
        try:
            db = SessionLocal()
            try:
                query = db.query(RBIUpdate)
                
                if new_only:
                    query = query.filter(RBIUpdate.is_new == True)
                
                updates = query.order_by(
                    RBIUpdate.date_published.desc()
                ).limit(limit).all()

                return [{
                    "title": update.title,
                    "press_release_link": update.press_release_link,
                    "pdf_link": update.pdf_link,
                    "date_published": update.date_published.isoformat() if update.date_published else None,
                    "date_scraped": update.date_scraped.isoformat(),
                    "is_new": update.is_new
                } for update in updates]

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error getting updates from database: {e}")
            return []

    def mark_as_read(self, press_release_link: str):
        """Mark an update as read (not new)"""
        try:
            db = SessionLocal()
            try:
                update = db.query(RBIUpdate).filter_by(
                    press_release_link=press_release_link
                ).first()
                
                if update:
                    update.is_new = False
                    db.commit()
                    
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error marking update as read: {e}")