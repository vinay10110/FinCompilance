import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from datetime import datetime

def get_clerk_users():
    """Get all users from Clerk"""
    clerk_secret = os.getenv('CLERK_SECRET_KEY')
    headers = {
        'Authorization': f'Bearer {clerk_secret}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            'https://api.clerk.dev/v1/users',
            headers=headers
        )
        response.raise_for_status()
        users = response.json()
        return [user['email_addresses'][0]['email_address'] for user in users if user.get('email_addresses')]
    except Exception as e:
        print(f"Error getting Clerk users: {str(e)}")
        return []

def send_update_notification(updates):
    """
    Send email notifications about new RBI updates to registered users.
    
    Args:
        updates (list): List of new updates to notify about
    """
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    # Get all registered users
    user_emails = get_clerk_users()
    if not user_emails:
        print("No registered users found to notify")
        return
    
    # Create email content
    subject = f"New RBI Updates Available - {datetime.now().strftime('%Y-%m-%d')}"
    
    email_body = "New RBI updates are available:\n\n"
    for update in updates:
        email_body += f"- {update['title']}\n"
        email_body += f"  Date: {update.get('date', 'N/A')}\n"
        if update.get('pdf_link'):
            email_body += f"  Document: {update['pdf_link']}\n"
        email_body += "\n"
    
    email_body += "\nVisit the FinCompliance dashboard to view these updates in detail.\n"
    
    try:
        # Create SMTP connection
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        # Send email to each user
        for email in user_emails:
            try:
                msg = MIMEMultipart()
                msg['From'] = smtp_username
                msg['To'] = email
                msg['Subject'] = subject
                
                msg.attach(MIMEText(email_body, 'plain'))
                
                server.send_message(msg)
                print(f"✉️ Notification sent to {email}")
                
            except Exception as e:
                print(f"Error sending to {email}: {str(e)}")
                continue
        
        server.quit()
        print("✅ All notifications sent successfully")
        
    except Exception as e:
        print(f"❌ Error sending notifications: {str(e)}")
