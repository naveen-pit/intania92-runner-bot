"""Test utils functions."""
import datetime
from typing import Self

import pytest
from linebot.models import MessageEvent, SourceGroup, SourceRoom, SourceUser

from running_bot.main import get_chat_id
from running_bot.utils import get_current_month, is_change_month, is_leaderboard_format, is_valid_month_string


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


@pytest.mark.usefixtures("_patch_datetime_now")
def test_is_change_month():
    # Test when the month has not changed
    month_string = "July 2024"
    assert not is_change_month(month_string)

    # Test when the month has changed
    month_string = "June 2024"
    assert is_change_month(month_string)


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
