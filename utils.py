"""Utility functions."""
from datetime import datetime, timedelta

def get_current_month(timezone_hour_diff = 7, date_format="%B %Y"):
    return (datetime.now()+ timedelta(hours=timezone_hour_diff)).strftime(date_format)

def is_change_month(month_string):
    return get_current_month() != month_string.strip()