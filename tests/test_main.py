"""Test functions for main module."""

from decimal import Decimal

from linebot.models import MessageEvent, SourceGroup, SourceRoom, SourceUser, TextMessage

from running_bot.main import (
    handle_leaderboard_update,
    is_leaderboard_format,
    parse_stats,
    process_message_event,
    update_distance_in_database,
)


def test_is_leaderboard_format():
    assert is_leaderboard_format("===Leaderboard")
    assert not is_leaderboard_format("Leaderboard")


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

    message_list = ["===TITLE", "SUBTITLE", "1 John a5 km"]
    user = "John"
    increase_distance = Decimal("5")
    expected_output = "Parse distance error, distance format is incorrect."
    assert parse_stats(message_list, user, increase_distance) == expected_output, "Invalid distance in leaderboard"


def test_handle_leaderboard_update(mocker):
    messages = "===TITLE\nSUBTITLE\n1 John 5\n2 Jane 10"
    expected_output = "===TITLE\nSUBTITLE\n1 Jane 10\n2 John 5"
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_leaderboard", return_value={"stats": messages})
    mocker.patch("running_bot.main.set_leaderboard", return_value=None)
    mock_event = MessageEvent(message=TextMessage(text="===Leaderboard"), source=SourceRoom(room_id="room_id"))
    assert handle_leaderboard_update(messages, mock_event) == expected_output


def test_handle_distance_update_with_error(mocker):
    chat_id = "test_chat_id"
    mocker.patch(
        "running_bot.main.get_leaderboard",
        return_value={"stats": "===Running Challenge===\nJuly 2024\n1 Jane 10 km\n2 John 5 km"},
    )
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)

    name = "John"
    distance_string = ""
    expected_output = "Error parsing distance"
    assert update_distance_in_database(name, distance_string, chat_id, "+") == expected_output

    name = "John"
    distance_string = "3+a"
    expected_output = "Error parsing distance"
    assert update_distance_in_database(name, distance_string, chat_id, "+") == expected_output

    name = "John"
    distance_string = "3-1"
    expected_output = "Error parsing distance"
    assert update_distance_in_database(name, distance_string, chat_id, "+") == expected_output


def test_handle_distance_increment(mocker):
    name = "John"
    distance_string = "3"
    chat_id = "test_chat_id"

    mocker.patch(
        "running_bot.main.get_leaderboard",
        return_value={"stats": "===Running Challenge===\nJuly 2024\n1 Jane 10 km\n2 John 5 km"},
    )
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.set_leaderboard", return_value=None)
    mocker.patch("running_bot.main.is_change_month", return_value=False)

    expected_output = "===Running Challenge===\nJuly 2024\n1 Jane 10 km\n2 John 8 km"
    assert update_distance_in_database(name, distance_string, chat_id, "+") == expected_output

    mocker.patch("running_bot.main.is_change_month", return_value=True)
    mocker.patch("running_bot.main.get_current_month", return_value="August 2024")
    expected_output = "===Running Challenge===\nAugust 2024\n1 John 3 km"
    assert update_distance_in_database(name, distance_string, chat_id, "+") == expected_output


def test_handle_multiple_distance_increment(mocker):
    name = "John"
    distance_string = "1+1+1.5"
    chat_id = "test_chat_id"

    mocker.patch(
        "running_bot.main.get_leaderboard",
        return_value={"stats": "===Running Challenge===\nJuly 2024\n1 Jane 10 km\n2 John 5 km"},
    )
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.set_leaderboard", return_value=None)
    mocker.patch("running_bot.main.is_change_month", return_value=False)

    expected_output = "===Running Challenge===\nJuly 2024\n1 Jane 10 km\n2 John 8.5 km"
    assert update_distance_in_database(name, distance_string, chat_id, "+") == expected_output

    mocker.patch("running_bot.main.is_change_month", return_value=True)
    mocker.patch("running_bot.main.get_current_month", return_value="August 2024")
    expected_output = "===Running Challenge===\nAugust 2024\n1 John 3.5 km"
    assert update_distance_in_database(name, distance_string, chat_id, "+") == expected_output


def test_handle_multiple_distance_increment_with_negative(mocker):
    name = "John"
    distance_string = "1+1+-1.5"
    chat_id = "test_chat_id"

    mocker.patch(
        "running_bot.main.get_leaderboard",
        return_value={"stats": "===Running Challenge===\nJuly 2024\n1 Jane 10 km\n2 John 5 km"},
    )
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.set_leaderboard", return_value=None)
    mocker.patch("running_bot.main.is_change_month", return_value=False)

    expected_output = "===Running Challenge===\nJuly 2024\n1 Jane 10 km\n2 John 5.5 km"
    assert update_distance_in_database(name, distance_string, chat_id, "+") == expected_output

    mocker.patch("running_bot.main.is_change_month", return_value=True)
    mocker.patch("running_bot.main.get_current_month", return_value="August 2024")
    expected_output = "===Running Challenge===\nAugust 2024\n1 John 0.5 km"
    assert update_distance_in_database(name, distance_string, chat_id, "+") == expected_output


def test_handle_distance_decrease(mocker):
    name = "John"
    distance_string = "3"
    chat_id = "test_chat_id"

    mocker.patch(
        "running_bot.main.get_leaderboard",
        return_value={"stats": "===Running Challenge===\nJuly 2024\n1 Jane 10 km\n2 John 5 km"},
    )
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.set_leaderboard", return_value=None)
    mocker.patch("running_bot.main.is_change_month", return_value=False)

    expected_output = "===Running Challenge===\nJuly 2024\n1 Jane 10 km\n2 John 2 km"
    assert update_distance_in_database(name, distance_string, chat_id, "-") == expected_output

    mocker.patch("running_bot.main.is_change_month", return_value=True)
    mocker.patch("running_bot.main.get_current_month", return_value="August 2024")
    expected_output = "===Running Challenge===\nAugust 2024"
    assert update_distance_in_database(name, distance_string, chat_id, "-") == expected_output


def test_handle_multiple_distance_decrease(mocker):
    name = "John"
    distance_string = "1-1.5"
    chat_id = "test_chat_id"

    mocker.patch(
        "running_bot.main.get_leaderboard",
        return_value={"stats": "===Running Challenge===\nJuly 2024\n1 Jane 10 km\n2 John 5 km"},
    )
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.set_leaderboard", return_value=None)
    mocker.patch("running_bot.main.is_change_month", return_value=False)

    expected_output = "===Running Challenge===\nJuly 2024\n1 Jane 10 km\n2 John 2.5 km"
    assert update_distance_in_database(name, distance_string, chat_id, "-") == expected_output

    mocker.patch("running_bot.main.is_change_month", return_value=True)
    mocker.patch("running_bot.main.get_current_month", return_value="August 2024")
    expected_output = "===Running Challenge===\nAugust 2024"
    assert update_distance_in_database(name, distance_string, chat_id, "-") == expected_output


def test_handle_distance_update_no_leaderboard(mocker):
    name = "John"
    distance_string = "3"
    chat_id = "test_chat_id"

    mocker.patch(
        "running_bot.main.get_leaderboard",
        return_value=None,
    )
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.set_leaderboard", return_value=None)
    mocker.patch("running_bot.main.is_change_month", return_value=False)
    mocker.patch("running_bot.main.get_current_month", return_value="August")

    expected_output = "===Running Challenge===\nAugust\n1 John 3 km"
    assert update_distance_in_database(name, distance_string, chat_id, "+") == expected_output


def test_handle_distance_invalid_month(mocker):
    name = "John"
    distance_string = "3"
    chat_id = "test_chat_id"

    mocker.patch(
        "running_bot.main.get_leaderboard",
        return_value={"stats": "===Running Challenge===\nJuly\n1 Jane 10 km\n2 John 5 km"},
    )
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.set_leaderboard", return_value=None)
    mocker.patch("running_bot.main.get_current_month", return_value="August")

    expected_output = "===Running Challenge===\nJuly\n1 Jane 10 km\n2 John 8 km"
    assert update_distance_in_database(name, distance_string, chat_id, "+") == expected_output


def test_process_message_event_with_leaderboard_input(mocker):
    mocker.patch("running_bot.main.is_leaderboard_format", return_value=True)
    mocker.patch("running_bot.main.handle_leaderboard_update", return_value="Leaderboard updated")
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_name", return_value={"name": "John"})
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(message=TextMessage(text="===Leaderboard"), source=SourceUser(user_id="user_id"))

    result = process_message_event(mock_event, mock_line_bot_api)

    assert result == "Leaderboard updated"


def test_process_message_event_with_distance_update(mocker):
    mocker.patch("running_bot.main.is_leaderboard_format", return_value=False)
    mocker.patch("running_bot.main.handle_distance_update", return_value="Distance updated")
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_name", return_value={"name": "John"})
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(message=TextMessage(text="John +5"), source=SourceUser(user_id="user_id"))

    result = process_message_event(mock_event, mock_line_bot_api)

    assert result == "Distance updated"


def test_process__message_event_with_negative_distance_update(mocker):
    mocker.patch("running_bot.main.is_leaderboard_format", return_value=False)
    mocker.patch("running_bot.main.handle_distance_update", return_value="Distance updated")
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_name", return_value={"name": "John"})
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(message=TextMessage(text="John -5"), source=SourceUser(user_id="user_id"))

    result = process_message_event(mock_event, mock_line_bot_api)

    assert result == "Distance updated"


def test_process_message_event_with_non_text_message(mocker):
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_name", return_value={"name": "John"})
    mock_event = MessageEvent(message=None, source=SourceUser(user_id="user_id"))

    result = process_message_event(mock_event, mock_line_bot_api)

    assert result is None


def test_process_event_with_group_source(mocker):
    mocker.patch("running_bot.main.is_leaderboard_format", return_value=True)
    mocker.patch("running_bot.main.handle_leaderboard_update", return_value="Leaderboard updated")
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_name", return_value={"name": "John"})
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(message=TextMessage(text="===Leaderboard"), source=SourceGroup(group_id="group_id"))

    result = process_message_event(mock_event, mock_line_bot_api)

    assert result == "Leaderboard updated"


def test_process_event_with_room_source(mocker):
    mocker.patch("running_bot.main.is_leaderboard_format", return_value=True)
    mocker.patch("running_bot.main.handle_leaderboard_update", return_value="Leaderboard updated")
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_name", return_value={"name": "John"})
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(message=TextMessage(text="===Leaderboard"), source=SourceRoom(room_id="room_id"))

    result = process_message_event(mock_event, mock_line_bot_api)

    assert result == "Leaderboard updated"
