import requests
import logging

def send_telegram_notification(telegram_config: dict, report_body_html: str):
    """
    Sends a notification message to a Telegram chat.

    Args:
        telegram_config (dict): A dictionary containing Telegram bot settings.
                                Expected keys: 'bot_token', 'chat_id'.
        report_body_html (str): The HTML content of the message. Note that Telegram
                                supports a limited subset of HTML.
    """
    if not telegram_config.get('enabled', 'false').lower() == 'true':
        logging.info("Telegram notifications are disabled in the config. Skipping.")
        return

    try:
        bot_token = telegram_config['bot_token']
        chat_id = telegram_config['chat_id']

        if not bot_token or "your_telegram_bot_token" in bot_token:
            logging.error("Telegram bot_token is missing or still set to the default placeholder. Message not sent.")
            return

        logging.info(f"Attempting to send Telegram notification with token ending in ...{bot_token[-4:]} to chat ID {chat_id[:4]}...")

        # Basic conversion of HTML to a format Telegram prefers
        # Replace <br> with newlines, strip other tags
        message_text = report_body_html.replace('<br>', '\n').replace('<br/>', '\n')
        # A more robust regex to remove all html tags for plain text
        import re
        message_text = re.sub('<[^<]+?>', '', message_text)


        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message_text,
            'parse_mode': 'HTML' # Let Telegram handle the subset of HTML it supports. The text is now plain.
        }

        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        logging.info(f"Telegram notification sent successfully to chat ID {chat_id}.")

    except KeyError as e:
        logging.error(f"Telegram config is missing a required key: {e}. Please check your config.ini and secrets. Message not sent.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send Telegram notification: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while sending Telegram notification: {e}")
