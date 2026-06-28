"""
Earnings Calendar Generator
----------------------------
Fetches upcoming stock earnings dates from Yahoo Finance and generates
an iCal (.ics) file you can subscribe to in any calendar app.

Portfolio tickers get 7-day + day-of alerts.
Watchlist tickers are added without notifications.

Usage:
    python earnings_tracker.py
"""

import json
from datetime import datetime, timedelta, date
from icalendar import Calendar, Event, Alarm
import pytz
import yfinance as yf

# ========== CONFIGURATION ==========
PORTFOLIO_FILE = "portfolio.json"
WATCHLIST_FILE = "watchlist.json"
OUTPUT_ICS = "earnings.ics"

# Timezone for events (US Eastern - where most earnings happen)
EASTERN = pytz.timezone('US/Eastern')

# ========== FETCH EARNINGS FROM YAHOO FINANCE ==========
def get_earnings_date(ticker, company_override=None, industry_override=None):
    """
    Fetch the next earnings date for a given ticker using yfinance.
    Returns a tuple (date_str, company_name, industry) or (None, None, None).

    company_override / industry_override — use these when provided in the JSON,
    otherwise fall back to yfinance.
    """
    today = date.today()
    company_name = company_override or ticker
    industry = industry_override or ""

    try:
        stock = yf.Ticker(ticker)

        # Fetch company name from yfinance if not provided
        if not company_override:
            try:
                info = stock.info
                if info and isinstance(info, dict):
                    company_name = info.get('shortName') or info.get('longName') or ticker
            except Exception:
                pass

        # Fetch industry from yfinance if not provided
        if not industry_override:
            try:
                info = stock.info
                if info and isinstance(info, dict):
                    industry = info.get('industry') or ""
            except Exception:
                pass

        cal = stock.calendar

        if cal is not None and isinstance(cal, dict):
            earnings_dates = cal.get('Earnings Date')
            if earnings_dates:
                # Filter to future dates only, pick the earliest
                future_dates = [d for d in earnings_dates if isinstance(d, date) and d >= today]
                if future_dates:
                    return min(future_dates).strftime('%Y-%m-%d'), company_name, industry

        # Fallback: try earnings_dates (pandas Series with historical + future)
        try:
            ed = stock.earnings_dates
            if ed is not None and len(ed) > 0:
                future_dates = [d.date() for d in ed.index if isinstance(d, datetime) and d.date() >= today]
                if future_dates:
                    return min(future_dates).strftime('%Y-%m-%d'), company_name, industry
        except Exception:
            pass

        print(f"⚠️ No future earnings date found for {ticker}")
        return None, None, None

    except Exception as e:
        print(f"❌ Error fetching {ticker}: {e}")
        return None, None, None

# ========== CREATE CALENDAR EVENT ==========
def create_event(ticker, company_name, earnings_date, has_alerts, industry=""):
    """Create an iCalendar event for an earnings date"""
    event = Event()

    # Parse the date
    date_obj = datetime.strptime(earnings_date, '%Y-%m-%d')

    # Set event time to 4:00 PM ET (typical earnings release time)
    event_dt = EASTERN.localize(datetime(
        date_obj.year, date_obj.month, date_obj.day, 16, 0, 0
    ))

    # Event properties
    display_name = f"{company_name} ({ticker})" if company_name != ticker else ticker
    event.add('summary', f"📊 {display_name} Earnings")
    event.add('dtstart', event_dt)
    event.add('dtend', event_dt + timedelta(hours=1))  # 1 hour duration
    event.add('dtstamp', datetime.now(pytz.UTC))
    event.add('uid', f"{ticker}-{earnings_date}@earnings-tracker")

    # Build description with company name and industry
    desc_lines = [f"{company_name} ({ticker}) earnings report", f"Date: {earnings_date}"]
    if industry:
        desc_lines.append(f"Industry: {industry}")
    desc_lines.append("Source: Yahoo Finance")
    event.add('description', '\n'.join(desc_lines))

    # Add alerts
    if has_alerts:
        # Portfolio: 7-day + day-of alerts
        alarm_1_week = Alarm()
        alarm_1_week.add('trigger', timedelta(days=-7))
        alarm_1_week.add('action', 'DISPLAY')
        alarm_1_week.add('description', f"🔔 REMINDER: {company_name} ({ticker}) earnings in 1 week!")
        event.add_component(alarm_1_week)

        alarm_day_of = Alarm()
        alarm_day_of.add('trigger', timedelta(hours=0))
        alarm_day_of.add('action', 'DISPLAY')
        alarm_day_of.add('description', f"📈 TODAY: {company_name} ({ticker}) earnings at 4:00 PM ET")
        event.add_component(alarm_day_of)
    else:
        # Watchlist: day-of alert only
        alarm_day_of = Alarm()
        alarm_day_of.add('trigger', timedelta(hours=0))
        alarm_day_of.add('action', 'DISPLAY')
        alarm_day_of.add('description', f"📈 TODAY: {company_name} ({ticker}) earnings at 4:00 PM ET")
        event.add_component(alarm_day_of)

    return event

# ========== MAIN SCRIPT ==========
def main():
    print("🚀 Starting Earnings Calendar Generator...")

    # Load portfolio (with alerts)
    with open(PORTFOLIO_FILE, 'r') as f:
        portfolio_data = json.load(f)
        portfolio_tickers = portfolio_data['tickers']

    # Load watchlist (without alerts)
    with open(WATCHLIST_FILE, 'r') as f:
        watchlist_data = json.load(f)
        watchlist_tickers = watchlist_data['tickers']

    # Helper: normalize ticker entries (supports both strings and dicts)
    def parse_entry(entry):
        if isinstance(entry, str):
            return entry, None, None
        return entry['ticker'], entry.get('company'), entry.get('industry')

    # Combine all tickers (portfolio gets has_alerts=True, watchlist gets has_alerts=False)
    all_tickers = []
    for entry in portfolio_tickers:
        ticker, company, industry = parse_entry(entry)
        all_tickers.append((ticker, True, company, industry))  # True = has alerts
    for entry in watchlist_tickers:
        ticker, company, industry = parse_entry(entry)
        all_tickers.append((ticker, False, company, industry))  # False = no alerts

    # Create calendar
    cal = Calendar()
    cal.add('prodid', '-//Earnings Tracker//EN')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('name', 'Stock Earnings Calendar')
    cal.add('x-wr-calname', 'Stock Earnings Calendar')

    # Fetch earnings for each ticker
    successful = 0
    failed = 0

    for ticker, has_alerts, company_override, industry_override in all_tickers:
        print(f"🔍 Fetching earnings for {ticker}...")
        earnings_date, company_name, industry = get_earnings_date(
            ticker, company_override, industry_override
        )

        if earnings_date:
            event = create_event(ticker, company_name, earnings_date, has_alerts, industry)
            cal.add_component(event)
            alert_status = "🔔 7d + day-of" if has_alerts else "🔕 day-of only"
            print(f"   ✅ Added {company_name} ({ticker}) on {earnings_date} ({alert_status})")
            successful += 1
        else:
            print(f"   ❌ Could not find earnings for {ticker}")
            failed += 1

    # Save the calendar file
    with open(OUTPUT_ICS, 'wb') as f:
        f.write(cal.to_ical())

    print(f"\n📅 Calendar saved to {OUTPUT_ICS}")
    print(f"📊 Summary: {successful} events added, {failed} failed")
    print("✨ Done! Commit this file to GitHub and enable GitHub Pages.")

if __name__ == "__main__":
    main()
