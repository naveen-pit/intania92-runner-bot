"""Test functions for main module."""

from decimal import Decimal

from linebot.models import ImageMessage, MessageEvent, SourceGroup, SourceRoom, SourceUser, TextMessage, TextSendMessage

from running_bot.main import (
    handle_distance_update,
    handle_image_set_message,
    handle_leaderboard_update,
    handle_single_image_message,
    parse_stats,
    process_message_event,
    update_distance_in_database,
)


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


def test_handle_zero_distance(mocker):
    name = "John"
    distance_string = "0"
    chat_id = "test_chat_id"

    mocker.patch(
        "running_bot.main.get_leaderboard",
        return_value={"stats": "===Running Challenge===\nJuly 2024\n1 Jane 10 km\n2 John 5 km"},
    )
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.set_leaderboard", return_value=None)
    mocker.patch("running_bot.main.is_change_month", return_value=False)

    assert update_distance_in_database(name, distance_string, chat_id, "+") is None


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


def test_handle_distance_update_invalid_name_format(mocker):
    reply_message_list = []
    mock_event = MessageEvent(message=TextMessage(text="Long John + 5"), source=SourceUser(user_id="user_id"))
    # Mock extract_name_and_distance_from_message to return None values
    mocker.patch("running_bot.utils.extract_name_and_distance_from_message", return_value=(None, None))

    response = handle_distance_update("Long John + 5", mock_event, None, reply_message_list, "+")

    assert response == "Name contains space or has invalid format"


def test_handle_distance_update_new_name(mocker):
    reply_message_list = []
    mock_event = MessageEvent(message=TextMessage(text="===Leaderboard"), source=SourceUser(user_id="user_id"))
    # Mock the necessary functions and classes
    mocker.patch("running_bot.utils.extract_name_and_distance_from_message", return_value=("John", "50"))
    mocker.patch("running_bot.utils.get_chat_id", return_value="mock_chat_id")
    mocker.patch("running_bot.main.update_distance_in_database", return_value="Updated Leaderboard")
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.set_name")

    # Call the function with a new name (no stored name)
    response = handle_distance_update("John+50", mock_event, None, reply_message_list, "+")

    assert len(reply_message_list) == 1
    assert isinstance(reply_message_list[0], TextSendMessage)
    assert "Your name was set to John" in reply_message_list[0].text
    assert response == "Updated Leaderboard"


def test_handle_distance_update_existing_name(mocker):
    reply_message_list = []
    mock_event = MessageEvent(message=TextMessage(text="===Leaderboard"), source=SourceUser(user_id="user_id"))
    # Mock the necessary functions and classes
    mocker.patch("running_bot.utils.extract_name_and_distance_from_message", return_value=("John", "50km"))
    mocker.patch("running_bot.utils.get_chat_id", return_value="mock_chat_id")
    mocker.patch("running_bot.main.update_distance_in_database", return_value="Updated Leaderboard")

    # Call the function with a matching stored name
    stored_name = {"name": "John"}
    response = handle_distance_update("John+50", mock_event, stored_name, reply_message_list, "+")

    # Check that set_name was not called because the stored name matches
    assert len(reply_message_list) == 0
    mocker.patch("running_bot.main.set_name").assert_not_called()
    assert response == "Updated Leaderboard"


def test_process_message_event_with_leaderboard_input(mocker):
    mocker.patch("running_bot.main.is_leaderboard_format", return_value=True)
    mocker.patch("running_bot.main.handle_leaderboard_update", return_value="Updated Leaderboard")
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_name", return_value={"name": "John"})
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(message=TextMessage(text="===Leaderboard"), source=SourceUser(user_id="user_id"))

    result = process_message_event(mock_event, mock_line_bot_api)

    assert result == [TextSendMessage(text="Updated Leaderboard")]


def test_process_message_event_with_distance_update(mocker):
    mocker.patch("running_bot.main.is_leaderboard_format", return_value=False)
    mocker.patch("running_bot.main.handle_distance_update", return_value="Updated Leaderboard")
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_name", return_value={"name": "John"})
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(message=TextMessage(text="John +5"), source=SourceUser(user_id="user_id"))

    result = process_message_event(mock_event, mock_line_bot_api)

    assert result == [TextSendMessage(text="Updated Leaderboard")]


def test_process_message_event_with_negative_distance_update(mocker):
    mocker.patch("running_bot.main.is_leaderboard_format", return_value=False)
    mocker.patch("running_bot.main.handle_distance_update", return_value="Updated Leaderboard")
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_name", return_value={"name": "John"})
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(message=TextMessage(text="John -5"), source=SourceUser(user_id="user_id"))

    result = process_message_event(mock_event, mock_line_bot_api)

    assert result == [TextSendMessage(text="Updated Leaderboard")]


def test_process_message_event_with_name_containing_space(mocker):
    mocker.patch("running_bot.main.is_leaderboard_format", return_value=False)
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_name", return_value=None)
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(message=TextMessage(text="John Doe +5"), source=SourceUser(user_id="user_id"))

    result = process_message_event(mock_event, mock_line_bot_api)

    assert result == [TextSendMessage(text="Name contains space or has invalid format")]


def test_process_message_event_with_too_long_name(mocker):
    mocker.patch("running_bot.main.is_leaderboard_format", return_value=False)
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_name", return_value=None)
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(
        message=TextMessage(text="ThisIsTooLongLongName +5"), source=SourceUser(user_id="user_id")
    )

    result = process_message_event(mock_event, mock_line_bot_api)

    assert result == [TextSendMessage(text="Name contains space or has invalid format")]


def test_process_message_event_with_invalid_name(mocker):
    mocker.patch("running_bot.main.is_leaderboard_format", return_value=False)
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_name", return_value=None)
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(message=TextMessage(text="ThisIsInvalid\nName +5"), source=SourceUser(user_id="user_id"))

    result = process_message_event(mock_event, mock_line_bot_api)

    assert result == []


def test_process_message_event_with_zero_distance(mocker):
    mocker.patch("running_bot.main.is_leaderboard_format", return_value=False)
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_name", return_value={"name": "John"})
    mocker.patch("running_bot.main.set_name")

    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(message=TextMessage(text="Bob +0"), source=SourceUser(user_id="user_id"))

    result = process_message_event(mock_event, mock_line_bot_api)

    assert result == [
        TextSendMessage(
            text=(
                "Your name was set to Bob.\n"
                "Bot always uses your latest submitted name. To change your name, type 'Name+0'"
            )
        )
    ]


def test_process_message_event_with_non_text_message(mocker):
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_name", return_value={"name": "John"})
    mock_event = MessageEvent(message=None, source=SourceUser(user_id="user_id"))

    result = process_message_event(mock_event, mock_line_bot_api)

    assert result == []


def test_process_event_with_group_source(mocker):
    mocker.patch("running_bot.main.is_leaderboard_format", return_value=True)
    mocker.patch("running_bot.main.handle_leaderboard_update", return_value="Updated Leaderboard")
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_name", return_value={"name": "John"})
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(message=TextMessage(text="===Leaderboard"), source=SourceGroup(group_id="group_id"))

    result = process_message_event(mock_event, mock_line_bot_api)

    assert result == [TextSendMessage(text="Updated Leaderboard")]


def test_process_event_with_room_source(mocker):
    mocker.patch("running_bot.main.is_leaderboard_format", return_value=True)
    mocker.patch("running_bot.main.handle_leaderboard_update", return_value="Updated Leaderboard")
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_name", return_value={"name": "John"})
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(message=TextMessage(text="===Leaderboard"), source=SourceRoom(room_id="room_id"))

    result = process_message_event(mock_event, mock_line_bot_api)

    assert result == [TextSendMessage(text="Updated Leaderboard")]


def test_process_event_with_image_message(mocker):
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_name", return_value={"name": "John"})
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")
    mocker.patch("running_bot.main.handle_single_image_message", return_value="Updated Leaderboard")
    mock_event = MessageEvent(message=ImageMessage(), source=SourceRoom(room_id="room_id", user_id="user_id"))

    result = process_message_event(mock_event, mock_line_bot_api)

    assert result == [TextSendMessage(text="Updated Leaderboard")]


def test_process_event_with_image_set_message(mocker):
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_name", return_value={"name": "John"})
    mocker.patch("running_bot.main.handle_image_set_message", return_value="Updated Leaderboard")
    mock_line_bot_api = mocker.patch("running_bot.main.LineBotApi")

    mock_event = MessageEvent(
        message=ImageMessage(image_set={"id": "image_id"}), source=SourceRoom(room_id="room_id", user_id="user_id")
    )

    result = process_message_event(mock_event, mock_line_bot_api)

    assert result == [TextSendMessage(text="Updated Leaderboard")]


def test_handle_single_image_message_positive_distance(mocker):
    mock_leaderboard = "===TITLE\nSUBTITLE\n1 John 5\n2 Jane 10"
    mocker.patch("running_bot.main.io.BytesIO")
    mocker.patch("running_bot.main.Image.open")
    mocker.patch("running_bot.main.LineBotApi.get_message_content")
    mocker.patch("running_bot.main.extract_distance_from_image", return_value=Decimal("10"))
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_leaderboard", return_value={"stats": mock_leaderboard})
    mocker.patch("running_bot.main.set_leaderboard")

    stored_name = {"name": "John"}
    mock_event = MessageEvent(message=ImageMessage(), source=SourceRoom(room_id="room_id", user_id="user_id"))
    reply_message_list = []

    result = handle_single_image_message(mock_event, mocker.Mock(), stored_name, reply_message_list)

    assert result is not None
    assert len(reply_message_list) == 1
    assert reply_message_list[0].text == "John + 10"


def test_handle_single_image_message_zero_distance(mocker):
    mock_leaderboard = "===TITLE\nSUBTITLE\n1 John 5\n2 Jane 10"
    mocker.patch("running_bot.main.io.BytesIO")
    mocker.patch("running_bot.main.Image.open")
    mocker.patch("running_bot.main.LineBotApi.get_message_content")
    mocker.patch("running_bot.main.extract_distance_from_image", return_value=Decimal("0"))
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_leaderboard", return_value={"stats": mock_leaderboard})
    mocker.patch("running_bot.main.set_leaderboard")

    stored_name = {"name": "John"}
    mock_event = MessageEvent(message=ImageMessage(), source=SourceRoom(room_id="room_id", user_id="user_id"))
    reply_message_list = []

    result = handle_single_image_message(mock_event, mocker.Mock(), stored_name, reply_message_list)

    assert result is None
    assert len(reply_message_list) == 0


def test_handle_image_set_message_last_image(mocker):
    mock_leaderboard = "===TITLE\nSUBTITLE\n1 John 5\n2 Jane 10"
    mocker.patch("running_bot.main.io.BytesIO")
    mocker.patch("running_bot.main.Image.open")
    mocker.patch("running_bot.main.LineBotApi.get_message_content")
    mocker.patch("running_bot.main.extract_distance_from_image", return_value=Decimal("10"))
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_leaderboard", return_value={"stats": mock_leaderboard})
    mocker.patch("running_bot.main.set_leaderboard")

    get_image_queue = mocker.patch("running_bot.main.get_image_queue", return_value={"1": "5", "2": "7"})

    stored_name = {"name": "John"}

    mock_event = MessageEvent(
        message=ImageMessage(image_set={"id": "image_id", "index": 3, "total": 3}),
        source=SourceRoom(room_id="room_id", user_id="user_id"),
    )

    reply_message_list = []

    result = handle_image_set_message(mock_event, mocker.Mock(), stored_name, reply_message_list)

    assert result is not None
    assert len(reply_message_list) == 1
    assert reply_message_list[0].text == "John + 5 + 7 + 10"
    get_image_queue.assert_called_once()


# Test handle_image_set_message for intermediate images in the set
def test_handle_image_set_message_intermediate_image(mocker):
    mock_leaderboard = "===TITLE\nSUBTITLE\n1 John 5\n2 Jane 10"
    mocker.patch("running_bot.main.io.BytesIO")
    mocker.patch("running_bot.main.Image.open")
    mocker.patch("running_bot.main.LineBotApi.get_message_content")
    mocker.patch("running_bot.main.extract_distance_from_image", return_value=Decimal("10"))
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_leaderboard", return_value={"stats": mock_leaderboard})
    mocker.patch("running_bot.main.set_leaderboard")

    firestore_client = mocker.Mock()
    mocker.patch("running_bot.main.Firestore", return_value=firestore_client)

    upsert_image_queue = mocker.patch("running_bot.main.upsert_image_queue")
    get_image_queue = mocker.patch("running_bot.main.get_image_queue", return_value={"1": "5", "2": "7"})

    stored_name = {"name": "John"}

    mock_event = MessageEvent(
        message=ImageMessage(image_set={"id": "image_id", "index": 1, "total": 3}),
        source=SourceRoom(room_id="room_id", user_id="user_id"),
    )

    reply_message_list = []

    result = handle_image_set_message(mock_event, mocker.Mock(), stored_name, reply_message_list)

    assert result is None
    assert len(reply_message_list) == 0
    get_image_queue.assert_not_called()
    upsert_image_queue.assert_called_once_with(firestore_client, "image_id", key="1", value="10")


def test_handle_image_set_message_last_image_with_missing_data(mocker):
    mock_leaderboard = "===TITLE\nSUBTITLE\n1 John 5\n2 Jane 10"
    mocker.patch("running_bot.main.io.BytesIO")
    mocker.patch("running_bot.main.Image.open")
    mocker.patch("running_bot.main.LineBotApi.get_message_content")
    mocker.patch("running_bot.main.extract_distance_from_image", return_value=Decimal("10"))
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_leaderboard", return_value={"stats": mock_leaderboard})
    mocker.patch("running_bot.main.set_leaderboard")

    get_image_queue = mocker.patch("running_bot.main.get_image_queue", return_value={"1": "5"})

    stored_name = {"name": "John"}

    mock_event = MessageEvent(
        message=ImageMessage(image_set={"id": "image_id", "index": 3, "total": 3}),
        source=SourceRoom(room_id="room_id", user_id="user_id"),
    )

    reply_message_list = []

    result = handle_image_set_message(mock_event, mocker.Mock(), stored_name, reply_message_list)

    assert result is not None
    assert len(reply_message_list) == 1
    assert reply_message_list[0].text == "John + 5 + 0 + 10"
    get_image_queue.assert_called_once()


def test_handle_image_set_message_last_image_is_non_zero_with_missing_queue(mocker):
    mock_leaderboard = "===TITLE\nSUBTITLE\n1 John 5\n2 Jane 10"
    mocker.patch("running_bot.main.io.BytesIO")
    mocker.patch("running_bot.main.Image.open")
    mocker.patch("running_bot.main.LineBotApi.get_message_content")
    mocker.patch("running_bot.main.extract_distance_from_image", return_value=Decimal("10"))
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_leaderboard", return_value={"stats": mock_leaderboard})
    mocker.patch("running_bot.main.set_leaderboard")

    get_image_queue = mocker.patch("running_bot.main.get_image_queue", return_value=None)

    stored_name = {"name": "John"}

    mock_event = MessageEvent(
        message=ImageMessage(image_set={"id": "image_id", "index": 2, "total": 2}),
        source=SourceRoom(room_id="room_id", user_id="user_id"),
    )

    reply_message_list = []

    result = handle_image_set_message(mock_event, mocker.Mock(), stored_name, reply_message_list)

    assert result is not None
    assert len(reply_message_list) == 1
    assert reply_message_list[0].text == "John + 0 + 10"
    get_image_queue.assert_called_once()


def test_handle_image_set_message_last_image_is_zero_with_missing_queue(mocker):
    mock_leaderboard = "===TITLE\nSUBTITLE\n1 John 5\n2 Jane 10"
    mocker.patch("running_bot.main.io.BytesIO")
    mocker.patch("running_bot.main.Image.open")
    mocker.patch("running_bot.main.LineBotApi.get_message_content")
    mocker.patch("running_bot.main.extract_distance_from_image", return_value=Decimal("0"))
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_leaderboard", return_value={"stats": mock_leaderboard})
    mocker.patch("running_bot.main.set_leaderboard")

    get_image_queue = mocker.patch("running_bot.main.get_image_queue", return_value=None)

    stored_name = {"name": "John"}

    mock_event = MessageEvent(
        message=ImageMessage(image_set={"id": "image_id", "index": 3, "total": 3}),
        source=SourceRoom(room_id="room_id", user_id="user_id"),
    )

    reply_message_list = []

    result = handle_image_set_message(mock_event, mocker.Mock(), stored_name, reply_message_list)

    assert result is None
    assert len(reply_message_list) == 0
    get_image_queue.assert_called_once()


def test_handle_image_set_message_all_zeros(mocker):
    mock_leaderboard = "===TITLE\nSUBTITLE\n1 John 5\n2 Jane 10"
    mocker.patch("running_bot.main.io.BytesIO")
    mocker.patch("running_bot.main.Image.open")
    mocker.patch("running_bot.main.LineBotApi.get_message_content")
    mocker.patch("running_bot.main.extract_distance_from_image", return_value=Decimal("0"))
    mocker.patch("running_bot.google_cloud.Firestore.__init__", return_value=None)
    mocker.patch("running_bot.main.get_leaderboard", return_value={"stats": mock_leaderboard})
    mocker.patch("running_bot.main.set_leaderboard")

    get_image_queue = mocker.patch("running_bot.main.get_image_queue", return_value={"1": "0", "2": "0"})

    stored_name = {"name": "John"}

    mock_event = MessageEvent(
        message=ImageMessage(image_set={"id": "image_id", "index": 3, "total": 3}),
        source=SourceRoom(room_id="room_id", user_id="user_id"),
    )

    reply_message_list = []

    result = handle_image_set_message(mock_event, mocker.Mock(), stored_name, reply_message_list)

    assert result is None
    assert len(reply_message_list) == 0
    get_image_queue.assert_called_once()
