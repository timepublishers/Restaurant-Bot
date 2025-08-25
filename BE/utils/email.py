import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

async def send_otp_email(recipient_email: str, otp_code: int, restaurant_name: str):
    """Send OTP email to restaurant admin"""
    
    if not EMAIL_USER or not EMAIL_PASSWORD:
        raise ValueError("Email configuration not set")
    
    subject = f"Login OTP for {restaurant_name}"
    body = f"""
    Hello,
    
    Your login OTP for {restaurant_name} admin panel is:
    
    {otp_code}
    
    This code will expire in 10 minutes.
    
    If you didn't request this login, please ignore this email.
    
    Best regards,
    Restaurant Ordering System
    """
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = recipient_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, recipient_email, text)
        server.quit()
        print(f"OTP email sent successfully to {recipient_email}")
    except Exception as e:
        print(f"Failed to send OTP email: {str(e)}")
        raise e