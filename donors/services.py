from abc import ABC, abstractmethod
import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)

class BaseNotificationService(ABC):
    @abstractmethod
    def send_welcome_notification(self, donor) -> bool:
        """
        Sends a welcome/invitation notification.
        Returns:
            bool: True if successful, False otherwise.
        """
        pass

class EmailNotificationService(BaseNotificationService):
    def send_welcome_notification(self, donor) -> bool:
        if not donor.email:
            logger.warning(f"Donor {donor.name} does not have an email address. Skipping email.")
            return False
        
        subject = "🚩 Chanda Receipt & Celebration Invitation - SBVM Youth Adoni"
        
        # Prepare content parameters
        context = {
            'donor_name': donor.name,
            'amount': donor.amount,
            'event_date': "14th September 2026",
            'association_address': "Hanuman Nagar, Water Tank Line, Adoni",
            'payment_date': donor.payment_date or timezone.now()
        }
        
        # HTML email content using traditional ganesh festival styling
        html_message = render_to_string('donors/emails/welcome_email.html', context)
        
        # Plain text fallback
        plain_message = (
            f"🚩 SBVM YOUTH ASSOCIATION, ADONI 🚩\n"
            f"🪔 Vinayaka Chavithi Chanda Receipt & Invitation 🪔\n\n"
            f"Dear {donor.name},\n\n"
            f"🙏 Sincere thanks for your generous contribution of Rs. {donor.amount} towards Ganesh Chanda!\n\n"
            f"📅 Event Date: 14th September 2026\n"
            f"📍 Venue: Hanuman Nagar, Water Tank Line, Adoni\n\n"
            f"🌺 We warmly invite you and your family to join us for Pujas, Lord Ganesha's blessings, and Prasadam distribution!"
        )

        
        try:
            sent_count = send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[donor.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            if sent_count > 0:
                donor.notification_sent = True
                donor.notification_sent_at = timezone.now()
                donor.save(update_fields=['notification_sent', 'notification_sent_at'])
                logger.info(f"Welcome email successfully sent to {donor.email}.")
                return True
            else:
                logger.error(f"Failed to send email to {donor.email} (sent count is 0).")
                return False
                
        except Exception as e:
            logger.error(f"Error occurred while sending email to {donor.email}: {str(e)}")
            return False

class SMSNotificationService(BaseNotificationService):
    def send_welcome_notification(self, donor) -> bool:
        if not donor.mobile_number:
            logger.warning(f"Donor {donor.name} does not have a mobile number. Skipping SMS.")
            return False
            
        message = (
            f"SBVM YOUTH ADONI: Dear {donor.name}, thank you for your contribution of Rs.{donor.amount} for Vinayaka Chavithi. "
            f"We warmly invite you to the celebration on 14th Sept 2026 at Hanuman Nagar, Adoni."
        )
        
        api_key = getattr(settings, 'FAST2SMS_API_KEY', '')
        if not api_key:
            # Console fallback for local testing
            logger.info(f"\n======== [SMS CONSOLE FALLBACK] ========\n"
                        f"To: {donor.mobile_number}\n"
                        f"Message: {message}\n"
                        f"========================================\n")
            # Mark as sent for development convenience
            donor.notification_sent = True
            donor.notification_sent_at = timezone.now()
            donor.save(update_fields=['notification_sent', 'notification_sent_at'])
            return True
            
        # Fast2SMS HTTP Integration
        import urllib.request
        import urllib.parse
        import json
        
        url = "https://www.fast2sms.com/dev/bulkV2"
        params = {
            'authorization': api_key,
            'route': 'q',
            'message': message,
            'language': 'english',
            'flash': 0,
            'numbers': donor.mobile_number
        }
        
        try:
            full_url = f"{url}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                if res_data.get('return') is True:
                    donor.notification_sent = True
                    donor.notification_sent_at = timezone.now()
                    donor.save(update_fields=['notification_sent', 'notification_sent_at'])
                    logger.info(f"SMS successfully sent to {donor.mobile_number} via Fast2SMS.")
                    return True
                else:
                    logger.error(f"Fast2SMS API returned error: {res_data.get('message')}")
                    return False
        except Exception as e:
            logger.error(f"Error sending SMS via Fast2SMS: {str(e)}")
            return False

class WhatsAppNotificationService(BaseNotificationService):
    def send_welcome_notification(self, donor) -> bool:
        if not donor.mobile_number:
            logger.warning(f"Donor {donor.name} does not have a mobile number. Skipping WhatsApp.")
            return False
            
        message = (
            f"🚩 *SBVM YOUTH ASSOCIATION, ADONI* 🚩\n"
            f"🪔 *Vinayaka Chavithi Chanda Receipt & Invitation* 🪔\n\n"
            f"Dear *{donor.name}*,\n\n"
            f"🙏 Sincere thanks for your generous contribution of *₹{donor.amount}* towards Ganesh Chanda!\n\n"
            f"📅 *Event Date:* 14th September 2026\n"
            f"📍 *Venue:* Hanuman Nagar, Water Tank Line, Adoni\n\n"
            f"🌺 We warmly invite you and your family to join us for Pujas, Lord Ganesha's blessings, and Prasadam distribution!"
        )


        
        account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        from_whatsapp = getattr(settings, 'TWILIO_WHATSAPP_NUMBER', '')
        
        if not account_sid or not auth_token:
            # Console fallback for local testing
            logger.info(f"\n======== [WHATSAPP CONSOLE FALLBACK] ========\n"
                        f"To: {donor.mobile_number}\n"
                        f"Message: {message}\n"
                        f"=============================================\n")
            # Mark as sent for development convenience
            donor.notification_sent = True
            donor.notification_sent_at = timezone.now()
            donor.save(update_fields=['notification_sent', 'notification_sent_at'])
            return True
            
        # Twilio WhatsApp HTTP Integration
        import urllib.request
        import urllib.parse
        import base64
        import json
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        
        # Clean mobile number: Twilio expects '+[country_code][number]'
        to_number = donor.mobile_number
        if not to_number.startswith('+'):
            to_number = f"+91{to_number[-10:]}"
            
        data = {
            'To': f"whatsapp:{to_number}",
            'From': from_whatsapp,
            'Body': message
        }
        
        payload = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(url, data=payload, method='POST')
        
        # HTTP Basic Authentication
        auth_str = f"{account_sid}:{auth_token}"
        auth_header = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
        req.add_header("Authorization", f"Basic {auth_header}")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        
        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                if res_data.get('status') in ['queued', 'sent']:
                    donor.notification_sent = True
                    donor.notification_sent_at = timezone.now()
                    donor.save(update_fields=['notification_sent', 'notification_sent_at'])
                    logger.info(f"WhatsApp message successfully queued/sent to {donor.mobile_number} via Twilio.")
                    return True
                else:
                    logger.error(f"Twilio API returned status: {res_data.get('status')}")
                    return False
        except Exception as e:
            logger.error(f"Error sending WhatsApp via Twilio: {str(e)}")
            return False

def get_notification_service(channel='email') -> BaseNotificationService:
    """
    Factory function to retrieve notification service implementation based on the channel.
    """
    if channel == 'email':
        return EmailNotificationService()
    elif channel == 'sms':
        return SMSNotificationService()
    elif channel == 'whatsapp':
        return WhatsAppNotificationService()
    raise ValueError(f"Unknown notification channel: {channel}")
