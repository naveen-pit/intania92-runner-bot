"""Test utils functions."""

import datetime
from typing import Self

import pytest

from utils import get_current_month, is_change_month


@pytest.fixture(autouse=True)
def _patch_datetime_now(monkeypatch) -> None:
    class MockDatetime(datetime.datetime):
        @classmethod
        def now(cls: type[Self], tz: datetime.tzinfo | None = None) -> datetime.datetime:
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


@pytest.mark.usefixtures("_patch_datetime_now")
def test_is_change_month():
    # Test when the month has not changed
    month_string = "July 2024"
    assert not is_change_month(month_string)

    # Test when the month has changed
    month_string = "June 2024"
    assert is_change_month(month_string)


if __name__ == "__main__":
    pytest.main()
