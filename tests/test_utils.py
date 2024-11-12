"""Test utils functions."""
import datetime
from typing import Self

import pytest
from linebot.models import MessageEvent, SourceGroup, SourceRoom, SourceUser

from running_bot.main import get_chat_id
from running_bot.utils import (
    contains_only_decimal,
    extract_name_and_distance_from_message,
    get_current_month,
    is_change_month,
    is_leaderboard_format,
    is_valid_month_string,
    is_valid_name,
    is_valid_update_distance_message,
)


@pytest.fixture(autouse=True)
def _patch_datetime_now(monkeypatch) -> None:
    class MockDatetime(datetime.datetime):
        @classmethod
        def now(cls: type[Self], tz: datetime.tzinfo | None = None) -> "MockDatetime":
            return cls(2024, 7, 15, 0, 0, 0, tzinfo=tz)

    monkeypatch.setattr(datetime, "datetime", MockDatetime)


@pytest.mark.usefixtures("_patch_datetime_now")
def test_get_current_month():
    # Test with the default timezone_hour_diff and date_format
    expected_result = "July 2024"
    assert get_current_month() == expected_result

    # Test with a different timezone_hour_diff
    expected_result = "July 2024"
    assert get_current_month(timezone_hour_diff=0) == expected_result

    # Test with a different date_format
    expected_result = "07-2024"
    assert get_current_month(date_format="%m-%Y") == expected_result


def test_is_valid_month_string():
    # test correct format
    month_string = "July 2024"
    assert is_valid_month_string(month_string)

    # test wrong format
    month_string = "July"
    assert not is_valid_month_string(month_string)

    # test wrong format
    month_string = "2024 July"
    assert not is_valid_month_string(month_string)

    # test irrelevant text
    month_string = "Week5"
    assert not is_valid_month_string(month_string)


def test_valid_update_distance_messages():
    """Test valid update distance messages with different split symbols."""
    assert is_valid_update_distance_message("Alice+10.5", "+")
    assert is_valid_update_distance_message("Bob-23", "-")
    assert is_valid_update_distance_message("Charlie+0.01", "+")
    assert is_valid_update_distance_message("Alice+-10.5", "+")


def test_invalid_update_distance_messages():
    """Test invalid update distance messages with various reasons."""
    assert not is_valid_update_distance_message("", "+")  # Empty message
    assert not is_valid_update_distance_message("Alice", "+")  # Missing number
    assert not is_valid_update_distance_message("+10.5", "+")  # Missing name
    assert not is_valid_update_distance_message("Alice+ten", "+")  # Non-numeric number
    assert not is_valid_update_distance_message("Alice+\n10.5", "+")  # Newline in name
    assert not is_valid_update_distance_message("Alice+10.5-", "+")  # Extra split symbol
    assert not is_valid_update_distance_message("Alice+10.5+", "+")  # Extra split symbol
    assert not is_valid_update_distance_message("Alice+12345678901", "+")  # Too long distance


def test_contains_only_decimal():
    """Test helper function for decimal-only strings."""
    assert contains_only_decimal("10.5")
    assert contains_only_decimal("0.01")
    assert contains_only_decimal("100")
    assert not contains_only_decimal("10a")
    assert not contains_only_decimal("a10")
    assert not contains_only_decimal("10.a")


def test_valid_names():
    """Test valid names with different lengths and characters."""
    assert is_valid_name("Alice")
    assert is_valid_name("Bob123")
    assert is_valid_name("Charlie_D", max_name_length=10)


def test_invalid_names():
    """Test invalid names with various reasons."""
    assert not is_valid_name("")  # Empty name
    assert not is_valid_name("  ")  # Only spaces
    assert not is_valid_name("\n")  # Newline character
    assert not is_valid_name("Alice Bob")  # Space in name
    assert not is_valid_name("VeryLongNameIsInvalid", max_name_length=10)  # Exceeds max length


@pytest.mark.usefixtures("_patch_datetime_now")
def test_is_change_month():
    # Test when the month has not changed
    month_string = "July 2024"
    assert not is_change_month(month_string)

    # Test when the month has changed
    month_string = "June 2024"
    assert is_change_month(month_string)


@pytest.mark.parametrize(
    ("messages", "split_symbol", "expected_name", "expected_distance"),
    [
        ("John+50", "+", "John", "50"),
        ("Alice-100", "-", "Alice", "100"),
        ("Bob+ 30", "+", "Bob", "30"),
        ("Charlie+50", "+", "Charlie", "50"),
        ("+50km", "+", None, None),  # Invalid because name is missing
        ("David +50", "+", "David", "50"),
        ("Eve-50", "+", None, None),  # Invalid because the split symbol does not match
        ("Tom-30", "-", "Tom", "30"),
        ("Tom", "-", None, None),  # Invalid because there is no split symbol
    ],
)
def test_extract_name_and_distance_from_message(messages, split_symbol, expected_name, expected_distance):
    name, distance = extract_name_and_distance_from_message(messages, split_symbol)
    assert name == expected_name
    assert distance == expected_distance


def test_is_leaderboard_format():
    assert is_leaderboard_format("===Leaderboard")
    assert not is_leaderboard_format("Leaderboard")


def test_get_chat_id():
    # Test case 1: SourceGroup
    group_id = "group123"
    group_event = MessageEvent(source=SourceGroup(group_id=group_id))
    assert get_chat_id(group_event) == group_id

    # Test case 2: SourceRoom
    room_id = "room456"
    room_event = MessageEvent(source=SourceRoom(room_id=room_id))
    assert get_chat_id(room_event) == room_id

    # Test case 3: SourceUser
    user_id = "user789"
    user_event = MessageEvent(source=SourceUser(user_id=user_id))
    assert get_chat_id(user_event) == user_id
