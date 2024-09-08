"""Utility functions."""

import datetime
from typing import Literal

from linebot.models import MessageEvent, SourceGroup, SourceRoom


def get_current_month(timezone_hour_diff: int = 7, date_format: str = "%B %Y") -> str:
    return (datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=timezone_hour_diff)).strftime(date_format)


def is_valid_month_string(input_string: str, date_format: str = "%B %Y") -> bool:
    try:
        datetime.datetime.strptime(input_string, date_format).replace(tzinfo=datetime.UTC)
    except ValueError:
        return False
    else:
        return True


def extract_name_and_distance_from_message(
    messages: str, split_symbol: Literal["+", "-"]
) -> tuple[str | None, str | None]:
    elements = messages.split(split_symbol, 1)
    valid_length = 2
    if len(elements) != valid_length or not elements[0].strip() or " " in elements[0].strip():
        return None, None
    return elements[0].strip(), elements[1].strip()


def is_change_month(month_string: str) -> bool:
    return get_current_month() != month_string.strip()


def is_leaderboard_format(text: str) -> bool:
    return text.startswith("===")


def get_chat_id(event: MessageEvent) -> str:
    if isinstance(event.source, SourceGroup):
        return event.source.group_id
    if isinstance(event.source, SourceRoom):
        return event.source.room_id
    return event.source.user_id
