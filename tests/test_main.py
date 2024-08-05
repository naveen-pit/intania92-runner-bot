"""Test functions for main module."""

from decimal import Decimal

from linebot.models import MessageEvent, SourceGroup, SourceRoom, SourceUser, TextMessage

from running_bot.main import (
    handle_distance_update,
    handle_leaderboard_update,
    is_leaderboard_input,
    parse_stats,
    process_event,
)


def test_is_leaderboard_input():
    assert is_leaderboard_input("===Leaderboard")
    assert not is_leaderboard_input("Leaderboard")


def test_parse_stats():
    message_list = ["===TITLE", "SUBTITLE", "1 John 5 km", "2 Jane 10 km"]
    expected_output = "===TITLE\nSUBTITLE\n1 Jane 10 km\n2 John 5 km"
    assert parse_stats(message_list) == expected_output, "Leaderboard does not sort correctly"

    message_list = []
    expected_output = "Please set title and subtitle in the following format\n===TITLE \n SUBTITLE"
    assert parse_stats(message_list) == expected_output, "Invalid leaderboard does not throw error as expected."

    message_list = ["===TITLE", "SUBTITLE", "1 John 5 km", "2 Jane 10 km"]
    user = "John"
    increase_distance = Decimal("5")
    expected_output = "===TITLE\nSUBTITLE\n1 John 10 km\n2 Jane 10 km"
    assert parse_stats(message_list, user, increase_distance) == expected_output, "Distance was not added correctly."

    message_list = ["===TITLE", "SUBTITLE", "1 John 5 km", "2 Jane 10 km"]
    user = "John"
    increase_distance = Decimal("-1")
    expected_output = "===TITLE\nSUBTITLE\n1 Jane 10 km\n2 John 4 km"
    assert (
        parse_stats(message_list, user, increase_distance) == expected_output
    ), "Negative distance was not subtracted correctly."

    message_list = ["===TITLE", "SUBTITLE", "1 John 5 km", "2 Jane 10 km"]
    user = "John"
    increase_distance = Decimal("-5")
    expected_output = "===TITLE\nSUBTITLE\n1 Jane 10 km"
    assert parse_stats(message_list, user, increase_distance) == expected_output, "Zero distance was not removed."

    message_list = ["===TITLE", "SUBTITLE"]
    user = "John"
    increase_distance = Decimal("5")
    expected_output = "===TITLE\nSUBTITLE\n1 John 5 km"
    assert parse_stats(message_list, user, increase_distance) == expected_output, "New user was not added."


def test_handle_leaderboard_update(mocker):
    messages = "===TITLE\nSUBTITLE\n1 John 5\n2 Jane 10"
    chat_id = "test_chat_id"
    expected_output = "===TITLE\nSUBTITLE\n1 Jane 10\n2 John 5"

    mocker.patch("running_bot.main.get_leaderboard", return_value={"stats": messages})
    mocker.patch("running_bot.main.set_leaderboard", return_value=None)

    assert handle_leaderboard_update(messages, chat_id) == expected_output


def test_handle_distance_update(mocker):
    messages = "John +3"
    chat_id = "test_chat_id"

    mocker.patch(
        "running_bot.main.get_leaderboard",
        return_value={"stats": "===92 Running Challenge===\nJuly\n1 Jane 10 km\n2 John 5 km"},
    )
    mocker.patch("running_bot.main.set_leaderboard", return_value=None)
    mocker.patch("running_bot.main.is_change_month", return_value=False)

    expected_output = "===92 Running Challenge===\nJuly\n1 Jane 10 km\n2 John 8 km"
    assert handle_distance_update(messages, chat_id) == expected_output

    mocker.patch("running_bot.main.is_change_month", return_value=True)
    mocker.patch("running_bot.main.get_current_month", return_value="August")
    expected_output = "===92 Running Challenge===\nAugust\n1 John 3 km"
    assert handle_distance_update(messages, chat_id) == expected_output


def test_process_event_with_leaderboard_input(mocker):
    mocker.patch("running_bot.main.is_leaderboard_input", return_value=True)
    mocker.patch("running_bot.main.handle_leaderboard_update", return_value="Leaderboard updated")
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(message=TextMessage(text="===Leaderboard"), source=SourceUser(user_id="user_id"))

    result = process_event(mock_event, mock_line_bot_api)

    assert result == "Leaderboard updated"


def test_process_event_with_distance_update(mocker):
    mocker.patch("running_bot.main.is_leaderboard_input", return_value=False)
    mocker.patch("running_bot.main.handle_distance_update", return_value="Distance updated")
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(message=TextMessage(text="John +5"), source=SourceUser(user_id="user_id"))

    result = process_event(mock_event, mock_line_bot_api)

    assert result == "Distance updated"


def test_process_event_with_non_text_message(mocker):
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(message=None, source=SourceUser(user_id="user_id"))

    result = process_event(mock_event, mock_line_bot_api)

    assert result is None


def test_process_event_with_non_message_event(mocker):
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    class DummyEvent:
        pass

    mock_event = DummyEvent()

    result = process_event(mock_event, mock_line_bot_api)

    assert result is None


def test_process_event_with_group_source(mocker):
    mocker.patch("running_bot.main.is_leaderboard_input", return_value=True)
    mocker.patch("running_bot.main.handle_leaderboard_update", return_value="Leaderboard updated")
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(message=TextMessage(text="===Leaderboard"), source=SourceGroup(group_id="group_id"))

    result = process_event(mock_event, mock_line_bot_api)

    assert result == "Leaderboard updated"


def test_process_event_with_room_source(mocker):
    mocker.patch("running_bot.main.is_leaderboard_input", return_value=True)
    mocker.patch("running_bot.main.handle_leaderboard_update", return_value="Leaderboard updated")
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(message=TextMessage(text="===Leaderboard"), source=SourceRoom(room_id="room_id"))

    result = process_event(mock_event, mock_line_bot_api)

    assert result == "Leaderboard updated"
