import requests
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client
import os
from zoneinfo import ZoneInfo

# ───────── CONFIG ─────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ist = ZoneInfo("Asia/Kolkata")

BASE_URL = "https://www.nseindia.com"
HOLIDAY_API = "https://www.nseindia.com/api/holiday-master?type=trading"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

# ───────── FETCH HOLIDAYS ─────────
def fetch_holidays():
    session = requests.Session()
    session.headers.update(HEADERS)

    session.get(BASE_URL)
    response = session.get(HOLIDAY_API)

    data = response.json()

    holidays = set()

    for item in data.get("CM", []):
        date_str = item["tradingDate"]  # format: "26-Jan-2026"
        date_obj = datetime.strptime(date_str, "%d-%b-%Y").date()
        holidays.add(date_obj)

    return holidays


# ───────── BUILD CALENDAR ─────────
def build_calendar(year, holidays):
    start = datetime(year, 1, 1).date()
    end   = datetime(year, 12, 31).date()

    records = []

    current = start

    while current <= end:
        is_weekend = current.weekday() >= 5
        is_holiday = current in holidays

        is_trading = not (is_weekend or is_holiday)

        reason = None
        if is_weekend:
            reason = "Weekend"
        elif is_holiday:
            reason = "NSE Holiday"

        records.append({
            "date": str(current),
            "is_trading_day": is_trading,
            "reason": reason
        })

        current += timedelta(days=1)

    return records


# ───────── UPSERT ─────────
def upsert_calendar(records):
    supabase.table("trading_calendar").upsert(records).execute()


# ───────── MAIN ─────────
def main():
    year = datetime.now(ist).year

    print(f"Updating trading calendar for {year}...")

    holidays = fetch_holidays()

    records = build_calendar(year, holidays)

    upsert_calendar(records)

    print("Calendar updated successfully")


if __name__ == "__main__":
    main()