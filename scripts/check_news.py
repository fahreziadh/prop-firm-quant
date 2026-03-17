#!/usr/bin/env python3
"""Show upcoming high-impact news events for the week."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from src.data.news_calendar import get_news_events

def main():
    now = pd.Timestamp.now(tz="UTC")
    end = now + pd.Timedelta(days=7)
    
    events = get_news_events(now, end)
    high = events[events["impact"] == "high"] if not events.empty else events
    
    print(f"\n📰 High-Impact News Events: {now.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')}")
    print("=" * 70)
    
    if high.empty:
        print("No high-impact events found for this week.")
    else:
        for _, row in high.iterrows():
            dt = row["datetime"].strftime("%a %Y-%m-%d %H:%M UTC")
            print(f"  🔴 {dt}  |  {row['currency']}  |  {row['event_name']}")
    
    print()

if __name__ == "__main__":
    main()
