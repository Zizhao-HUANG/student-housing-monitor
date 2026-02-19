import asyncio
import logging
import schedule
import time
import os
import sys
from datetime import datetime

from config import load_config
from scrapers import (check_crous, check_estudines,
                        check_nexity, check_nemea,
                        check_lokaviz, check_adele)
from notifiers import send_email_notification, send_telegram_notification

# --- Scraper Mapping ---
SCRAPER_MAPPING = {
    "crous": check_crous,
    "estudines": check_estudines,
    "nexity": check_nexity,
    "nemea": check_nemea,
    "lokaviz": check_lokaviz,
    "adele": check_adele
}

def setup_logging():
    """Sets up logging to both file and console."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_filename = os.path.join(log_dir, f"scraper_{datetime.now().strftime('%Y-%m-%d')}.log")

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def format_report_html(results: list) -> str:
    """Formats the list of scraper results into an HTML report."""
    html = "<h1>每日房源检查报告</h1>"
    html += f"<p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
    html += "<hr>"

    for result in results:
        status_color = "green" if result['status'] == '有空房' else "red"
        # Use a more descriptive name for each report entry if available
        name = result.get('residence_name', result['name'])
        html += f"<h2>{name}</h2>"
        html += f"<p><b>状态: <span style='color:{status_color};'>{result['status']}</span></b></p>"
        # Using <pre> for details to preserve formatting (like newlines in lokaviz)
        html += f"<div><b>详情:</b><pre>{result['details']}</pre></div>"
        html += f"<p><a href='{result['url']}'>访问网站</a></p>"
        html += "<hr>"

    return html

async def run_check(config_path: str):
    """Runs all scrapers, formats the report, and sends notifications."""
    logging.info("Starting housing check run...")

    config = load_config(config_path)
    if not config:
        logging.error("Could not load configuration for this run.")
        return

    tasks = []
    # Check for URLS section
    if not config.has_section('URLS'):
        logging.error("Config file is missing the [URLS] section.")
        return

    urls_to_check = dict(config.items('URLS'))

    for name, url in urls_to_check.items():
        # Clean the key to match the scraper mapping (e.g., "adele_winston" -> "adele")
        scraper_key = name.split('_')[0].lower()
        scraper_func = SCRAPER_MAPPING.get(scraper_key)

        if scraper_func:
            # Pass both url and the original name for better reporting
            tasks.append(scraper_func(url, name))
        else:
            logging.warning(f"No scraper function found for key '{scraper_key}' from config entry '{name}'. Skipping.")

    results = await asyncio.gather(*tasks)

    logging.info("All scrapers finished. Generating report.")
    report_html = format_report_html(results)
    report_subject = f"房源报告 - {datetime.now().strftime('%Y-%m-%d')}"

    # Safely check for notifier sections before calling them
    if config.has_section('EMAIL'):
        send_email_notification(config['EMAIL'], report_subject, report_html)
    else:
        logging.warning("No [EMAIL] section in config, skipping email notification.")

    if config.has_section('TELEGRAM'):
        # The telegram notifier only needs the body of the report.
        send_telegram_notification(config['TELEGRAM'], report_html)
    else:
        logging.warning("No [TELEGRAM] section in config, skipping Telegram notification.")

    logging.info("Housing check run complete.")

def main():
    """Main function to load config and start the scheduler or run once."""
    try:
        setup_logging()
        logging.info("Application started.")

        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config.ini')

        if os.environ.get('CI') == 'true':
            logging.info("CI environment detected. Running the check once immediately.")
            asyncio.run(run_check(config_path))
        else:
            config = load_config(config_path)
            if not config:
                logging.critical("Could not load configuration. Exiting.")
                return

            schedule_time = config.get('GENERAL', 'SCHEDULE_TIME', fallback='14:15')
            logging.info(f"Local environment detected. Checks will run daily at {schedule_time}. Starting scheduler.")

            schedule.every().day.at(schedule_time).do(lambda: asyncio.run(run_check(config_path)))

            while True:
                schedule.run_pending()
                time.sleep(1)
    except Exception as e:
        logging.critical(f"An unhandled exception occurred in main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
