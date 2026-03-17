"""News event filter — skip trading around high-impact economic releases."""
import pandas as pd
import numpy as np


def is_news_blackout(timestamp, events_df, window_minutes=60):
    """Check if timestamp is within blackout window of any high-impact event.
    
    Args:
        timestamp: pd.Timestamp to check
        events_df: DataFrame from get_news_events()
        window_minutes: minutes before/after event to blackout
    
    Returns:
        True if in blackout window
    """
    if events_df.empty:
        return False
    
    ts = pd.Timestamp(timestamp)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    
    window = pd.Timedelta(minutes=window_minutes)
    
    for _, ev in events_df.iterrows():
        ev_time = ev["datetime"]
        if ev_time.tzinfo is None:
            ev_time = ev_time.tz_localize("UTC")
        if abs(ts - ev_time) <= window:
            return True
    return False


def add_news_blackout_column(price_df, events_df, window_minutes=60, impact_levels=None):
    """Add 'news_blackout' boolean column to price dataframe.
    
    Args:
        price_df: OHLCV DataFrame with DatetimeIndex
        events_df: DataFrame from get_news_events()
        window_minutes: blackout window in minutes
        impact_levels: list of impact levels to filter (default: ["high"])
    
    Returns:
        DataFrame with news_blackout column added
    """
    if impact_levels is None:
        impact_levels = ["high"]
    
    df = price_df.copy()
    df["news_blackout"] = False
    
    if events_df.empty:
        return df
    
    # Filter by impact level
    filtered = events_df[events_df["impact"].isin(impact_levels)]
    if filtered.empty:
        return df
    
    window = pd.Timedelta(minutes=window_minutes)
    
    # Vectorized approach: for each event, mark all bars within window
    idx = df.index
    if idx.tz is None:
        # Make tz-naive for comparison
        event_times = filtered["datetime"].dt.tz_localize(None) if filtered["datetime"].dt.tz is not None else filtered["datetime"]
    else:
        event_times = filtered["datetime"]
    
    blackout = np.zeros(len(df), dtype=bool)
    for ev_time in event_times:
        mask = np.abs((idx - ev_time).total_seconds()) <= window_minutes * 60
        blackout |= mask
    
    df["news_blackout"] = blackout
    return df
