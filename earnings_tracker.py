import json
import requests
import argparse
import os
import sys
from datetime import datetime, timedelta
from icalendar import Calendar, Event, Alarm
import pytz

# ========== CONFIGURATION ==========
CONFIG_FILE = "earnings_config.json"
PORTFOLIO_FILE = "portfolio.json"
WATCHLIST_FILE = "watchlist.json"
OUTPUT_ICS = "earnings.ics"

# Global API Key
FINNHUB_API_KEY = ""

# Timezone for events (US Eastern - where most earnings happen)
EASTERN = pytz.timezone('US/Eastern')

def load_config():
    global FINNHUB_API_KEY
    if not os.path.exists(CONFIG_FILE):
        print(f"⚠️ Config file {CONFIG_FILE} not found. Please run with -configure flag first.")
        # Fallback to the default key for now if the user hasn't configured it
        FINNHUB_API_KEY = "d8cq0hhr01qt0j1hs5e0d8cq0hhr01qt0j1hs5eg"
        return
    
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        FINNHUB_API_KEY = config.get("FINNHUB_API_KEY", "")

def configure_app():
    print("=== Earnings Tracker Configuration ===")
    api_key = input("Enter your Finnhub API Key: ").strip()
    
    config = {
        "FINNHUB_API_KEY": api_key,
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
        
    print(f"✅ Configuration saved to {CONFIG_FILE}")
    sys.exit(0)

# ========== FETCH EARNINGS FROM FINNHUB ==========
def get_earnings_date(ticker):
    """Fetch the next earnings date for a given ticker from Finnhub"""
    url = f"https://finnhub.io/api/v1/calendar/earnings?symbol={ticker}&token={FINNHUB_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # Finnhub returns earningsCalendar array
        earnings_list = data.get('earningsCalendar', [])
        
        if earnings_list and len(earnings_list) > 0:
            # Get the first upcoming earnings event
            earnings = earnings_list[0]
            earnings_date = earnings.get('date')
            
            # Estimate time (most earnings are after market close)
            # Finnhub doesn't always provide time, so we default to 4:00 PM ET
            return earnings_date
        else:
            print(f"⚠️ No earnings date found for {ticker}")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching {ticker}: {e}")
        return None

# ========== CREATE CALENDAR EVENT ==========
def create_event(ticker, earnings_date, has_alerts):
    """Create an iCalendar event for an earnings date"""
    event = Event()
    
    # Parse the date
    date_obj = datetime.strptime(earnings_date, '%Y-%m-%d')
    
    # Set event time to 4:00 PM ET (typical earnings release time)
    event_dt = EASTERN.localize(datetime(
        date_obj.year, date_obj.month, date_obj.day, 16, 0, 0
    ))
    
    # Event properties
    event.add('summary', f"📊 {ticker} Earnings Release")
    event.add('dtstart', event_dt)
    event.add('dtend', event_dt + timedelta(hours=1))  # 1 hour duration
    event.add('dtstamp', datetime.now(pytz.UTC))
    event.add('uid', f"{ticker}-{earnings_date}@earnings-tracker")
    event.add('description', f"Earnings report for {ticker}\nDate: {earnings_date}\nSource: Finnhub API")
    
    # Add alerts ONLY for portfolio tickers
    if has_alerts:
        # Alarm 1: 7 days before
        alarm_1_week = Alarm()
        alarm_1_week.add('trigger', timedelta(days=-7))
        alarm_1_week.add('action', 'DISPLAY')
        alarm_1_week.add('description', f"🔔 REMINDER: {ticker} earnings in 1 week!")
        event.add_component(alarm_1_week)
        
        # Alarm 2: Day of (0 hours before = at event time)
        alarm_day_of = Alarm()
        alarm_day_of.add('trigger', timedelta(hours=0))
        alarm_day_of.add('action', 'DISPLAY')
        alarm_day_of.add('description', f"📈 TODAY: {ticker} earnings releasing at 4:00 PM ET")
        event.add_component(alarm_day_of)
    
    return event

# ========== MAIN SCRIPT ==========
def main():
    parser = argparse.ArgumentParser(description="Generate Earnings Calendar")
    parser.add_argument('-configure', action='store_true', help='Configure the API key')
    args = parser.parse_args()

    if args.configure:
        configure_app()
        
    load_config()

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
        earnings_date = get_earnings_date(ticker)
        
        if earnings_date:
            event = create_event(ticker, earnings_date, has_alerts)
            cal.add_component(event)
            alert_status = "🔔 WITH ALERTS" if has_alerts else "🔕 no alerts"
            print(f"   ✅ Added {ticker} on {earnings_date} ({alert_status})")
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