# 📊 Earnings Calendar

> Auto-generate an iCal feed from upcoming stock earnings dates. Subscribe once in Apple or Google Calendar and never miss an earnings report again.

[![Update Earnings Calendar](https://github.com/mattc-try/finnhub-to-ics-calendar/actions/workflows/update-calendar.yml/badge.svg)](https://github.com/mattc-try/finnhub-to-ics-calendar/actions/workflows/update-calendar.yml)

## Features

- **Free & no API keys** — powered by Yahoo Finance via `yfinance`
- **Portfolio + Watchlist** — portfolio tickers get 7-day and day-of alerts; watchlist tickers are silent
- **International stocks** — works with US, HK, EU, UK, TW exchanges (e.g. `0001.HK`, `MC.PA`, `LSEG.L`, `TSM`)
- **Auto-updating** — GitHub Actions regenerates the calendar daily, old dates drop off automatically
- **Subscribe once** — works with Apple Calendar, Google Calendar, Outlook, or any iCal-compatible app

## Quick Start

```bash
# 1. Clone the repo
git clone git@github.com:mattc-try/finnhub-to-ics-calendar.git
cd finnhub-to-ics-calendar

# 2. Install dependencies
pip install -r requirements.txt

# 3. Edit your tickers
#    - portfolio.json  → tickers you hold (get alerts)
#    - watchlist.json  → tickers you're watching (no alerts)

# 4. Generate the calendar
python earnings_tracker.py
# → earnings.ics is created
```

## Configuration

### `portfolio.json`
Tickers you own. Events include **7-day and day-of notifications**.

```json
{
  "tickers": ["ADBE", "AMZN", "GOOGL", "NVDA", "0001.HK"]
}
```

### `watchlist.json`
Tickers you're tracking. Events are added **without alerts**.

```json
{
  "tickers": ["MSFT", "COST", "MC.PA", "TSM"]
}
```

## How It Works

```
portfolio.json ──┐
                 ├──> earnings_tracker.py ──> earnings.ics ──> Your calendar app
watchlist.json ──┘        (yfinance)            (iCal)
```

The script fetches the **next upcoming** earnings date for each ticker from Yahoo Finance, filters out past dates, and generates a complete `.ics` file. Each run replaces the entire calendar — no duplicates, no stale events.

## Automation

This repo includes a GitHub Actions workflow that runs **daily at 22:00 UTC** (after US markets close):

```
.github/workflows/update-calendar.yml
    ├── Checkout repo
    ├── Install dependencies
    ├── Run earnings_tracker.py
    └── Commit & push updated earnings.ics
```

You can also trigger it manually from the [Actions tab](https://github.com/mattc-try/finnhub-to-ics-calendar/actions).

## Subscribe in Your Calendar

### Option 1: GitHub Pages (recommended)
1. Enable GitHub Pages in your repo settings (Settings → Pages → Deploy from branch → `main`, `/ root`)
2. In your calendar app, subscribe to:
   ```
   https://<your-username>.github.io/<repo-name>/earnings.ics
   ```
3. Set auto-refresh to **every hour**

### Option 2: Local file
Open `earnings.ics` directly in Calendar.app to import as a static calendar. Re-run the script to refresh.

## File Structure

```
.
├── earnings_tracker.py          # Main script
├── portfolio.json               # Your holdings (with alerts)
├── watchlist.json               # Your watchlist (no alerts)
├── earnings.ics                 # Generated iCal file (auto-updated by CI)
├── requirements.txt             # Python dependencies
└── .github/workflows/
    └── update-calendar.yml      # GitHub Actions daily runner
```

## Requirements

- Python 3.9+
- `yfinance` — Yahoo Finance data
- `icalendar` — iCal file generation
- `pytz` — timezone handling
