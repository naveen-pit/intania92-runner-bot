"""Utility functions."""

import datetime
import re
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


def is_valid_update_distance_message(
    message: str, split_symbol: Literal["+", "-"], max_characters_in_decimal: int = 10
) -> bool:
    """
    Check valid update distance message.

    Valid distance message should contain <NAME><split_symbol><NUMBER>.
    """
    elements = message.split(split_symbol)
    minimum_element_count = 2
    if len(elements) < minimum_element_count:
        return False
    if not elements[0].strip() or "\n" in elements[0].strip():
        return False
    return all(
        len(elements[i]) < max_characters_in_decimal and contains_only_decimal(elements[i])
        for i in range(1, len(elements))
    )


def is_valid_name(name: str, max_name_length: int = 15, not_allowed_char_tuple: tuple[str, ...] = (" ", "\n")) -> bool:
    return len(name) > 0 and len(name) <= max_name_length and all(s not in name for s in not_allowed_char_tuple)


def contains_only_decimal(text: str) -> bool:
    # Pattern matches valid numbers with optional negative sign and decimal point
    pattern = r"^-?\d*\.?\d+$"
    return bool(re.match(pattern, text))


def extract_name_and_distance_from_message(
    messages: str, split_symbol: Literal["+", "-"]
) -> tuple[str | None, str | None]:
    if split_symbol in messages:
        elements = messages.split(split_symbol, 1)
        if is_valid_name(elements[0].strip()):
            return elements[0].strip(), elements[1].strip()
    return None, None


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
