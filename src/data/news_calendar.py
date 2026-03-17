"""Economic news calendar data fetcher."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import calendar
import json
import urllib.request


def _first_friday(year, month):
    """Get first Friday of a month."""
    cal = calendar.monthcalendar(year, month)
    # Friday is index 4
    first_fri = cal[0][4] if cal[0][4] != 0 else cal[1][4]
    return date(year, month, first_fri)


def _get_recurring_events(start_date, end_date):
    """Generate recurring high-impact economic events."""
    events = []
    
    # FOMC dates 2024-2026 (hardcoded from Fed schedule)
    fomc_dates = [
        # 2024
        "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12",
        "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
        # 2025
        "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18",
        "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-17",
        # 2026
        "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17",
        "2026-07-29", "2026-09-16", "2026-11-04", "2026-12-16",
    ]
    
    for d in fomc_dates:
        dt = pd.Timestamp(d + " 18:00:00", tz="UTC")
        if start_date <= dt <= end_date:
            events.append({"datetime": dt, "event_name": "FOMC Rate Decision",
                          "impact": "high", "currency": "USD"})
    
    # Generate monthly recurring events
    current = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    
    while current <= end:
        y, m = current.year, current.month
        
        # NFP: First Friday, 13:30 UTC
        nfp_date = _first_friday(y, m)
        nfp_dt = pd.Timestamp(f"{nfp_date} 13:30:00", tz="UTC")
        if start_date <= nfp_dt <= end_date:
            events.append({"datetime": nfp_dt, "event_name": "Non-Farm Payrolls",
                          "impact": "high", "currency": "USD"})
        
        # CPI: ~13th of month, 13:30 UTC
        cpi_day = min(13, calendar.monthrange(y, m)[1])
        cpi_dt = pd.Timestamp(f"{y}-{m:02d}-{cpi_day:02d} 13:30:00", tz="UTC")
        if start_date <= cpi_dt <= end_date:
            events.append({"datetime": cpi_dt, "event_name": "CPI",
                          "impact": "high", "currency": "USD"})
        
        # GDP: ~28th of month, 13:30 UTC
        gdp_day = min(28, calendar.monthrange(y, m)[1])
        gdp_dt = pd.Timestamp(f"{y}-{m:02d}-{gdp_day:02d} 13:30:00", tz="UTC")
        if start_date <= gdp_dt <= end_date:
            events.append({"datetime": gdp_dt, "event_name": "GDP",
                          "impact": "high", "currency": "USD"})
        
        # PPI: ~15th of month
        ppi_day = min(15, calendar.monthrange(y, m)[1])
        ppi_dt = pd.Timestamp(f"{y}-{m:02d}-{ppi_day:02d} 13:30:00", tz="UTC")
        if start_date <= ppi_dt <= end_date:
            events.append({"datetime": ppi_dt, "event_name": "PPI",
                          "impact": "high", "currency": "USD"})
        
        # Advance to next month
        if m == 12:
            current = pd.Timestamp(f"{y+1}-01-01", tz="UTC")
        else:
            current = pd.Timestamp(f"{y}-{m+1:02d}-01", tz="UTC")
    
    return events


def _fetch_forex_factory():
    """Try to fetch this week's events from Forex Factory JSON feed."""
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        
        events = []
        for item in data:
            impact = item.get("impact", "").lower()
            if impact not in ("high", "medium", "low"):
                impact = "medium"
            
            # Parse date
            date_str = item.get("date", "")
            if not date_str:
                continue
            try:
                dt = pd.Timestamp(date_str, tz="UTC")
            except Exception:
                continue
            
            events.append({
                "datetime": dt,
                "event_name": item.get("title", "Unknown"),
                "impact": impact,
                "currency": item.get("country", "USD"),
            })
        return events
    except Exception:
        return []


def get_news_events(start_date, end_date):
    """Get economic news events between start_date and end_date.
    
    Returns DataFrame with columns: datetime, event_name, impact, currency
    """
    if isinstance(start_date, str):
        start_date = pd.Timestamp(start_date, tz="UTC")
    if isinstance(end_date, str):
        end_date = pd.Timestamp(end_date, tz="UTC")
    
    # Ensure tz-aware
    if start_date.tzinfo is None:
        start_date = start_date.tz_localize("UTC")
    if end_date.tzinfo is None:
        end_date = end_date.tz_localize("UTC")
    
    # Get recurring events
    events = _get_recurring_events(start_date, end_date)
    
    # Try to supplement with Forex Factory live data
    ff_events = _fetch_forex_factory()
    for ev in ff_events:
        if start_date <= ev["datetime"] <= end_date:
            events.append(ev)
    
    if not events:
        return pd.DataFrame(columns=["datetime", "event_name", "impact", "currency"])
    
    df = pd.DataFrame(events)
    df = df.drop_duplicates(subset=["datetime", "event_name"]).sort_values("datetime").reset_index(drop=True)
    return df
