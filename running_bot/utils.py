"""Utility functions."""

import datetime


def get_current_month(timezone_hour_diff: int = 7, date_format: str = "%B %Y") -> str:
    return (datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=timezone_hour_diff)).strftime(date_format)


def is_change_month(month_string: str) -> bool:
    return get_current_month() != month_string.strip()
