import os
import requests
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SlackNotifier:
    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not self.webhook_url:
            print("⚠️ SLACK_WEBHOOK_URL not found in environment variables")

    def send_notification(self, message: str, title: str = "FinCompliance Update") -> bool:
        """
        Send a basic notification to Slack
        """
        if not self.webhook_url:
            print("❌ Cannot send notification: Slack webhook URL not configured")
            return False

        payload = {
            "text": f"*{title}*\n{message}",
            "username": "FinCompliance Bot",
            "icon_emoji": ":bank:"
        }

        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Slack notification sent successfully")
                return True
            else:
                print(f"❌ Failed to send Slack notification: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending Slack notification: {str(e)}")
            return False

    def send_circular_updates(self, new_circulars: List[Dict[str, Any]]) -> bool:
        """
        Send notification about new RBI circulars
        """
        if not new_circulars:
            return True

        count = len(new_circulars)
        title = f"🏦 New RBI Circular{'s' if count > 1 else ''} Available"
        
        message_parts = [
            f"Found {count} new circular{'s' if count > 1 else ''}:",
            ""
        ]

        for circular in new_circulars[:5]:  # Limit to first 5 to avoid long messages
            category = circular.get('category', 'Unknown')
            title_text = circular.get('title', 'No title')
            date_published = circular.get('date_published', 'Unknown date')
            
            # Truncate long titles
            if len(title_text) > 80:
                title_text = title_text[:80] + "..."
            
            message_parts.append(f"• *{category}*")
            message_parts.append(f"  {title_text}")
            message_parts.append(f"  📅 {date_published}")
            message_parts.append("")

        if count > 5:
            message_parts.append(f"... and {count - 5} more circular{'s' if count - 5 > 1 else ''}")

        message_parts.append(f"🔗 Check the FinCompliance dashboard for full details")
        
        message = "\n".join(message_parts)
        return self.send_notification(message, title)

    def send_press_release_updates(self, new_releases: List[Dict[str, Any]]) -> bool:
        """
        Send notification about new RBI press releases
        """
        if not new_releases:
            return True

        count = len(new_releases)
        title = f"📰 New RBI Press Release{'s' if count > 1 else ''} Available"
        
        message_parts = [
            f"Found {count} new press release{'s' if count > 1 else ''}:",
            ""
        ]

        for release in new_releases[:3]:  # Limit to first 3 for press releases
            title_text = release.get('title', 'No title')
            date_published = release.get('date_published', 'Unknown date')
            
            # Truncate long titles
            if len(title_text) > 80:
                title_text = title_text[:80] + "..."
            
            message_parts.append(f"• {title_text}")
            message_parts.append(f"  📅 {date_published}")
            message_parts.append("")

        if count > 3:
            message_parts.append(f"... and {count - 3} more release{'s' if count - 3 > 1 else ''}")

        message_parts.append(f"🔗 Check the FinCompliance dashboard for full details")
        
        message = "\n".join(message_parts)
        return self.send_notification(message, title)

    def send_error_notification(self, error_message: str, context: str = "System Error") -> bool:
        """
        Send error notification to Slack
        """
        title = f"🚨 FinCompliance Error - {context}"
        message = f"An error occurred:\n```{error_message}```"
        return self.send_notification(message, title)

    def send_system_notification(self, message: str, title: str = "System Notification") -> bool:
        """
        Send general system notification
        """
        return self.send_notification(message, f"🔔 {title}")


# Global notifier instance
notifier = SlackNotifier()

# Convenience functions
def notify_new_circulars(circulars: List[Dict[str, Any]]) -> bool:
    """Notify about new RBI circulars"""
    return notifier.send_circular_updates(circulars)

def notify_new_press_releases(releases: List[Dict[str, Any]]) -> bool:
    """Notify about new RBI press releases"""
    return notifier.send_press_release_updates(releases)

def notify_error(error: str, context: str = "System Error") -> bool:
    """Send error notification"""
    return notifier.send_error_notification(error, context)

def notify_system(message: str, title: str = "System Notification") -> bool:
    """Send system notification"""
    return notifier.send_system_notification(message, title)
