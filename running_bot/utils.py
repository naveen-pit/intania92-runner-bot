"""Utility functions."""

import datetime


def get_current_month(timezone_hour_diff: int = 7, date_format: str = "%B %Y") -> str:
    return (datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=timezone_hour_diff)).strftime(date_format)


def is_valid_month_string(input_string: str, date_format: str = "%B %Y") -> bool:
    try:
        datetime.datetime.strptime(input_string, date_format).replace(tzinfo=datetime.UTC)
    except ValueError:
        return False
    else:
        return True


def is_change_month(month_string: str) -> bool:
    return get_current_month() != month_string.strip()
