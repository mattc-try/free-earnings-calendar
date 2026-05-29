# Earnings Calendar Tracker

A Python script that generates a `.ics` calendar from stock earnings dates. It separates your portfolio (with notifications) from a watchlist (without notifications).

## Features
- Fetches upcoming earnings dates using the Finnhub API.
- Differentiates between portfolio tickers (get alerts) and watchlist tickers (no alerts).
- Can be synced with Apple Calendar, Google Calendar, etc.
- Interactive `-configure` flag to set up your API key.

## Requirements
- `requests`
- `icalendar`
- `pytz`

Install dependencies:
```bash
pip install requests icalendar pytz
```

## Usage

1. **Configure your API Key:**
   ```bash
   python earnings_tracker.py -configure
   ```

2. **Run the script:**
   ```bash
   python earnings_tracker.py
   ```

3. **Output:**
   The calendar is generated as `earnings.ics` in the same directory as the script.

## Next Steps for Automation
- Host `earnings.ics` via GitHub Pages.
- Subscribe to the raw URL in your calendar app.
- Automate updates daily using GitHub Actions.
