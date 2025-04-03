# notifications/integrations/twilio.py
from twilio.rest import Client
from django.conf import settings
import logging

# Initialize logger for the module
logger = logging.getLogger(__name__)

def send_sms(to_number, message):
    """
    Sends an SMS message using the Twilio API.

    :param to_number: The recipient's phone number (e.g., '+1234567890')
    :param message: The message to be sent
    :return: Message SID if successful, else None
    """
    try:
        # Validate Twilio settings
        twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        twilio_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        twilio_phone = getattr(settings, 'TWILIO_PHONE_NUMBER', None)

        if not (twilio_sid and twilio_token and twilio_phone):
            logger.error("Twilio settings are not properly configured.")
            return None

        # Initialize the Twilio client
        client = Client(twilio_sid, twilio_token)
        
        # Send the SMS
        message_instance = client.messages.create(
            body=message,
            from_=twilio_phone,
            to=to_number
        )
        logger.info(f"SMS sent successfully to {to_number}: SID {message_instance.sid}")
        return message_instance.sid

    except Exception as e:
        logger.error(f"Failed to send SMS to {to_number}: {e}")
        return None
