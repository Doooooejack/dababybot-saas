#!/usr/bin/env python3
"""
Test script to verify email configuration for DababyBot
Run this to test if your SMTP settings are working correctly.
"""

import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

def test_email_config():
    """Test email configuration"""
    print("🔧 Testing DababyBot Email Configuration")
    print("=" * 50)

    # Load environment variables
    load_dotenv()
    print("✅ Loaded .env file")

    # Get email settings
    email_from = os.getenv('EMAIL_FROM', '').strip()
    email_password = os.getenv('EMAIL_PASSWORD', '').strip()
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com').strip()
    smtp_port_str = os.getenv('SMTP_PORT', '465').strip()

    print(f"📧 EMAIL_FROM: {email_from}")
    print(f"🔒 EMAIL_PASSWORD: {'***SET***' if email_password else 'NOT SET'}")
    print(f"🌐 SMTP_HOST: {smtp_host}")
    print(f"🔌 SMTP_PORT: {smtp_port_str}")

    # Validate configuration
    if not email_from:
        print("❌ ERROR: EMAIL_FROM is not set!")
        return False

    if not email_password:
        print("❌ ERROR: EMAIL_PASSWORD is not set!")
        return False

    if not smtp_host:
        print("❌ ERROR: SMTP_HOST is not set!")
        return False

    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        print(f"❌ ERROR: Invalid SMTP_PORT: {smtp_port_str}")
        return False

    # Test email connection
    print("\n📤 Testing SMTP connection...")
    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as server:
            print("🔗 Connected to SMTP server")
            server.login(email_from, email_password)
            print("✅ Authentication successful")

            # Send test email
            msg = MIMEText("This is a test email from DababyBot configuration test.")
            msg["Subject"] = "DababyBot Email Test"
            msg["From"] = f"DababyBot <{email_from}>"
            msg["To"] = email_from

            server.sendmail(email_from, [email_from], msg.as_string())
            print("✅ Test email sent successfully!")
            print(f"📬 Check your inbox at: {email_from}")

    except Exception as e:
        print(f"❌ SMTP Error: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. For Gmail: Make sure you're using an App Password, not your regular password")
        print("2. Enable 2-Factor Authentication on your Google account")
        print("3. Generate App Password: https://myaccount.google.com/apppasswords")
        print("4. Use the 16-character password (no spaces) in EMAIL_PASSWORD")
        return False

    print("\n🎉 Email configuration is working correctly!")
    print("Your DababyBot registration emails should now be sent successfully.")
    return True

if __name__ == "__main__":
    test_email_config()