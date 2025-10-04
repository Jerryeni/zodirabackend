"""
Firebase Email Service for ZODIRA Backend

This service provides comprehensive email functionality with:
- Firebase Admin SDK integration
- SMTP email delivery with multiple providers
- OTP email templates
- Enhanced debugging and logging
- Fallback mechanisms for reliability
"""

import firebase_admin
from firebase_admin import credentials, auth
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import os
from typing import Optional, Dict, Any
import logging
from datetime import datetime
from app.config.settings import settings

from email.message import EmailMessage

logger = logging.getLogger(__name__)

class FirebaseEmailService:
    """Comprehensive email service with Firebase integration"""
    
    def __init__(self):
        # SMTP Configuration
        self.smtp_server = os.getenv('FIREBASE_SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('FIREBASE_SMTP_PORT', '465'))
        use_ssl_str = os.getenv('FIREBASE_SMTP_USE_SSL', 'true')
        self.smtp_use_ssl = str(use_ssl_str).lower() in ('1', 'true', 'yes')
        self.email_user = os.getenv('FIREBASE_EMAIL_USER', settings.zodira_support_email)
        self.email_password = os.getenv('FIREBASE_EMAIL_PASSWORD', '')
        # Email templates
        self.from_name = "ZODIRA Support"
        self.from_email = self.email_user

        logger.info(f"Firebase Email Service initialized")
        logger.info(f"SMTP Server: {self.smtp_server}:{self.smtp_port} (SSL: {self.smtp_use_ssl})")
        logger.info(f"From Email: {self.from_email}")
    

    async def send_otp_email(self, to_email: str, otp_code: str) -> bool:
        """
        Send OTP email using configured SMTP settings.
        Returns True on success, False on failure.
        """
        try:
            if not self.email_user or not self.email_password:
                logger.warning("SMTP not configured (FIREBASE_EMAIL_USER/PASSWORD missing)")
                return False

            msg = EmailMessage()
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            msg["Subject"] = "Your ZODIRA Verification Code"

            # Compose message
            text_body = self._create_text_otp_email(otp_code)
            html_body = self._create_html_otp_email(otp_code)
            msg.set_content(text_body)
            msg.add_alternative(html_body, subtype="html")

            if self.smtp_use_ssl:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as smtp:
                    smtp.login(self.email_user, self.email_password)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as smtp:
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.login(self.email_user, self.email_password)
                    smtp.send_message(msg)

            logger.info(f"OTP email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"OTP email delivery failed for {to_email}: {e}")
            return False
    
    def _create_text_otp_email(self, otp_code: str) -> str:
        """Create plain text OTP email"""
        return f"""
Hello,

Your ZODIRA verification code is: {otp_code}

This code will expire in 5 minutes for your security.

Please enter this code in the app to complete your authentication.

If you didn't request this code, please ignore this email.

Best regards,
ZODIRA Team
Support: {settings.zodira_support_email}
        """.strip()
    
    def _create_html_otp_email(self, otp_code: str) -> str:
        """Create HTML OTP email template"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Your ZODIRA Verification Code</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .otp-code {{ background: #fff; border: 2px solid #667eea; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; color: #667eea; margin: 20px 0; border-radius: 10px; letter-spacing: 5px; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 14px; }}
        .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌟 ZODIRA</h1>
            <p>Your Cosmic Journey Awaits</p>
        </div>
        <div class="content">
            <h2>Verification Code</h2>
            <p>Hello,</p>
            <p>Your ZODIRA verification code is:</p>
            
            <div class="otp-code">{otp_code}</div>
            
            <div class="warning">
                <strong>⚠️ Security Notice:</strong>
                <ul>
                    <li>This code expires in <strong>5 minutes</strong></li>
                    <li>Never share this code with anyone</li>
                    <li>ZODIRA will never ask for this code via phone or email</li>
                </ul>
            </div>
            
            <p>If you didn't request this code, please ignore this email and contact our support team.</p>
            
            <div class="footer">
                <p>Best regards,<br>
                <strong>ZODIRA Team</strong></p>
                <p>Support: {settings.zodira_support_email}</p>
                <p><em>Connecting you with the cosmos</em></p>
            </div>
        </div>
    </div>
</body>
</html>
        """.strip()
    
    async def send_welcome_email(self, to_email: str, user_name: str) -> bool:
        """Send welcome email to new users"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = "Welcome to ZODIRA - Your Cosmic Journey Begins!"
            
            # Create welcome email content
            html_body = self._create_welcome_email_html(user_name)
            text_body = self._create_welcome_email_text(user_name)
            
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            if self.email_user and self.email_password:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.sendmail(self.from_email, to_email, msg.as_string())
                server.quit()
                
                logger.info(f"✅ Welcome email sent to {to_email}")
                return True
            else:
                logger.info(f"📧 Welcome email would be sent to {to_email} (SMTP not configured)")
                return True
                
        except Exception as e:
            logger.error(f"❌ Welcome email failed for {to_email}: {e}")
            return False
    
    def _create_welcome_email_text(self, user_name: str) -> str:
        """Create plain text welcome email"""
        return f"""
Welcome to ZODIRA, {user_name}!

Thank you for joining our cosmic community. Your journey into the world of Vedic astrology and cosmic insights begins now.

What you can do with ZODIRA:
- Get personalized daily, weekly, and monthly predictions
- Discover marriage compatibility through detailed Guna Milan analysis
- Consult with expert astrologers
- Explore your birth chart and planetary influences

Get started by completing your profile and exploring your cosmic insights.

Best regards,
ZODIRA Team
Support: {settings.zodira_support_email}
        """.strip()
    
    def _create_welcome_email_html(self, user_name: str) -> str:
        """Create HTML welcome email template"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Welcome to ZODIRA</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .feature {{ background: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #667eea; }}
        .cta {{ background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌟 Welcome to ZODIRA</h1>
            <p>Your Cosmic Journey Begins Now</p>
        </div>
        <div class="content">
            <h2>Hello {user_name}!</h2>
            <p>Thank you for joining our cosmic community. We're excited to guide you through the fascinating world of Vedic astrology and cosmic insights.</p>
            
            <h3>What you can explore with ZODIRA:</h3>
            
            <div class="feature">
                <strong>🔮 Personalized Predictions</strong><br>
                Get daily, weekly, and monthly cosmic insights tailored to your birth chart
            </div>
            
            <div class="feature">
                <strong>💑 Marriage Compatibility</strong><br>
                Discover relationship compatibility through detailed Guna Milan analysis
            </div>
            
            <div class="feature">
                <strong>👨‍🏫 Expert Consultations</strong><br>
                Connect with experienced Vedic astrologers for personalized guidance
            </div>
            
            <div class="feature">
                <strong>📊 Birth Chart Analysis</strong><br>
                Explore your planetary influences and astrological profile
            </div>
            
            <p>Ready to begin your cosmic journey?</p>
            <a href="https://zodira.app/dashboard" class="cta">Explore Your Cosmic Profile</a>
            
            <div class="footer">
                <p>Best regards,<br>
                <strong>ZODIRA Team</strong></p>
                <p>Support: {settings.zodira_support_email}</p>
                <p><em>Connecting you with the cosmos</em></p>
            </div>
        </div>
    </div>
</body>
</html>
        """.strip()
    
    async def test_email_configuration(self) -> Dict[str, Any]:
        """Test email configuration and connectivity"""
        try:
            logger.info("🔍 Testing email configuration...")
            
            if not self.email_user or not self.email_password:
                return {
                    "status": "warning",
                    "message": "SMTP credentials not configured - using development mode",
                    "smtp_server": self.smtp_server,
                    "smtp_port": self.smtp_port,
                    "configured": False
                }
            
            # Test SMTP connection
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.quit()
            
            logger.info("✅ Email configuration test successful")
            return {
                "status": "success",
                "message": "Email service configured and working",
                "smtp_server": self.smtp_server,
                "smtp_port": self.smtp_port,
                "configured": True
            }
            
        except Exception as e:
            logger.error(f"❌ Email configuration test failed: {e}")
            return {
                "status": "error",
                "message": f"Email configuration failed: {str(e)}",
                "smtp_server": self.smtp_server,
                "smtp_port": self.smtp_port,
                "configured": False,
                "error": str(e)
            }

# Global email service instance
firebase_email_service = FirebaseEmailService()