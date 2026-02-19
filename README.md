# Student Housing Monitor

An automated multi-site student housing availability scraper for Strasbourg, France. Scrapes six different housing platforms simultaneously and sends email/Telegram notifications when vacancies are found.

## Motivation

Finding student housing in Strasbourg during peak season is extremely competitive — rooms disappear within hours. This tool automates the monitoring process by checking multiple platforms on a schedule and sending instant notifications when availability is detected.

## Supported Platforms

| Platform | Method | Status |
|----------|--------|--------|
| **CROUS** | Keyword detection | ✅ Working |
| **Les Estudines** | Button/text detection | ✅ Working |
| **Lokaviz** | Date-based listing filter | ✅ Working |
| **Adele** | Availability section parsing | ✅ Working |
| **Néméa** | Text pattern matching | ✅ Working |
| **Nexity Studéa** | CloudFront protected | ⚠️ Blocked |

All scrapers use [Playwright](https://playwright.dev/) for headless browser automation, enabling JavaScript rendering and dynamic content extraction.

## Architecture

```
┌──────────────────────────────────────┐
│         main.py (Orchestrator)       │
│  ┌──────────┐ ┌───────────────────┐  │
│  │ Scheduler│ │ Async Scrape Loop │  │
│  └──────────┘ └───────────────────┘  │
└──────────────┬───────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│ CROUS  │ │Lokaviz │ │ Adele  │  ... (6 scrapers)
└────────┘ └────────┘ └────────┘
               │
               ▼
    ┌─────────────────────┐
    │   HTML Report Gen   │
    └─────────┬───────────┘
              │
    ┌─────────┼──────────┐
    ▼                    ▼
┌────────┐        ┌──────────┐
│ Email  │        │ Telegram │
└────────┘        └──────────┘
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r housing_scraper/requirements.txt
playwright install --with-deps chromium
```

### 2. Configure

```bash
cp housing_scraper/config.ini.example housing_scraper/config.ini
```

Edit `config.ini` with your notification credentials and target URLs.

### 3. Run

```bash
# Run once
CI=true python housing_scraper/main.py

# Run on schedule (default: daily at 14:15)
python housing_scraper/main.py
```

### 4. GitHub Actions (Optional)

The included workflow (`.github/workflows/main.yml`) supports:
- ⏰ Scheduled runs (configurable cron)
- 🔘 Manual trigger via GitHub UI

Store your credentials as GitHub Secrets and update the workflow to use `config.ini` from secrets.

## How It Works

1. **Scraping** — Each scraper function launches a headless Chromium browser, navigates to the target URL, and extracts availability information using platform-specific selectors and patterns
2. **Report Generation** — Results are compiled into an HTML report with color-coded availability status (green = available, red = no vacancy)
3. **Notification** — The report is sent via configured channels (Email via SMTP, Telegram Bot API)

## Configuration

See `config.ini.example` for all available options:

- `[URLS]` — Housing platform URLs to monitor (easily add new targets)
- `[EMAIL]` — SMTP configuration for email notifications
- `[TELEGRAM]` — Bot token and chat ID for Telegram alerts
- `[GENERAL]` — Schedule timing

## License

This project is for personal and educational use.
