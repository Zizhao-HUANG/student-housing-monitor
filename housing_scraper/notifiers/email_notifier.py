import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_notification(smtp_config: dict, report_subject: str, report_body_html: str):
    """
    Sends a notification email.

    Args:
        smtp_config (dict): A dictionary containing SMTP server settings.
                           Expected keys: 'server', 'port', 'user', 'password', 'recipient'.
        report_subject (str): The subject of the email.
        report_body_html (str): The HTML content of the email body.
    """
    if not smtp_config.get('enabled', 'false').lower() == 'true':
        logging.info("Email notifications are disabled in the config. Skipping.")
        return

    try:
        # Use more descriptive keys consistent with the config file
        user = smtp_config['smtp_user']
        password = smtp_config['smtp_password']
        recipient = smtp_config['recipient_email']
        server_addr = smtp_config['smtp_server']
        port_str = smtp_config.get('smtp_port')

        if not port_str or not port_str.isdigit():
            logging.error(f"Invalid or missing SMTP port: '{port_str}'. Email not sent.")
            return

        port = int(port_str)

        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = recipient
        msg['Subject'] = report_subject

        msg.attach(MIMEText(report_body_html, 'html'))

        with smtplib.SMTP(server_addr, port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
            logging.info(f"Email notification sent successfully to {recipient}.")

    except KeyError as e:
        logging.error(f"Email config is missing a required key: {e}. Please check your config.ini and secrets. Email not sent.")
    except Exception as e:
        logging.error(f"Failed to send email notification: {e}")
