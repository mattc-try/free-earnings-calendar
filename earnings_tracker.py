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
def get_earnings_date(ticker):
    """
    Fetch the next earnings date and company name for a given ticker using yfinance.
    Returns a tuple (date_str, company_name) or (None, None).
    """
    today = date.today()

    try:
        stock = yf.Ticker(ticker)

        # Fetch company name
        company_name = ticker
        try:
            info = stock.info
            if info and isinstance(info, dict):
                company_name = info.get('shortName') or info.get('longName') or ticker
        except Exception:
            pass

        cal = stock.calendar

        if cal is not None and isinstance(cal, dict):
            earnings_dates = cal.get('Earnings Date')
            if earnings_dates:
                # Filter to future dates only, pick the earliest
                future_dates = [d for d in earnings_dates if isinstance(d, date) and d >= today]
                if future_dates:
                    return min(future_dates).strftime('%Y-%m-%d'), company_name

        # Fallback: try earnings_dates (pandas Series with historical + future)
        try:
            ed = stock.earnings_dates
            if ed is not None and len(ed) > 0:
                future_dates = [d.date() for d in ed.index if isinstance(d, datetime) and d.date() >= today]
                if future_dates:
                    return min(future_dates).strftime('%Y-%m-%d'), company_name
        except Exception:
            pass

        print(f"⚠️ No future earnings date found for {ticker}")
        return None, None

    except Exception as e:
        print(f"❌ Error fetching {ticker}: {e}")
        return None, None

# ========== CREATE CALENDAR EVENT ==========
def create_event(ticker, company_name, earnings_date, has_alerts):
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
    event.add('description', f"{company_name} ({ticker}) earnings report\nDate: {earnings_date}\nSource: Yahoo Finance")

    # Add alerts ONLY for portfolio tickers
    if has_alerts:
        # Alarm 1: 7 days before
        alarm_1_week = Alarm()
        alarm_1_week.add('trigger', timedelta(days=-7))
        alarm_1_week.add('action', 'DISPLAY')
        alarm_1_week.add('description', f"🔔 REMINDER: {company_name} ({ticker}) earnings in 1 week!")
        event.add_component(alarm_1_week)

        # Alarm 2: Day of (0 hours before = at event time)
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

    # Combine all tickers (portfolio gets alerts=True, watchlist gets alerts=False)
    all_tickers = []
    for ticker in portfolio_tickers:
        all_tickers.append((ticker, True))  # True = has alerts
    for ticker in watchlist_tickers:
        all_tickers.append((ticker, False))  # False = no alerts

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

    for ticker, has_alerts in all_tickers:
        print(f"🔍 Fetching earnings for {ticker}...")
        earnings_date, company_name = get_earnings_date(ticker)

        if earnings_date:
            event = create_event(ticker, company_name, earnings_date, has_alerts)
            cal.add_component(event)
            alert_status = "🔔 WITH ALERTS" if has_alerts else "🔕 no alerts"
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
