"""Test main function."""

from unittest.mock import MagicMock, patch

import pytest
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent

from running_bot.main import main


@pytest.fixture()
def mock_cfg():
    with patch("running_bot.config") as mock_cfg:
        mock_cfg.line_channel_secret_key.get_secret_value.return_value = "mock_channel_secret"
        mock_cfg.line_access_token.get_secret_value.return_value = "mock_access_token"
        yield mock_cfg


@pytest.fixture()
def mock_request():
    request = MagicMock()
    request.headers = {"X-Line-Signature": "mock_signature"}
    request.get_data.return_value = "mock_body"
    return request


@pytest.fixture()
def mock_line_bot_api():
    with patch("running_bot.main.LineBotApi") as mock_line_bot_api_class:
        mock_line_bot_api = mock_line_bot_api_class.return_value
        yield mock_line_bot_api


@pytest.fixture()
def mock_parser():
    with patch("running_bot.main.WebhookParser") as mock_webhook_parser_class:
        mock_parser = mock_webhook_parser_class.return_value
        yield mock_parser


@pytest.fixture()
def mock_process_message_event():
    with patch("running_bot.main.process_message_event") as mock_process_message_event:
        yield mock_process_message_event


def test_main_success(mock_cfg, mock_request, mock_line_bot_api, mock_parser, mock_process_message_event):
    # Mock the parse method to return a list of events
    mock_event = MagicMock(spec=MessageEvent)
    mock_parser.parse.return_value = [mock_event]

    # Call the main function
    response = main(mock_request)

    # Assertions
    mock_parser.parse.assert_called_once_with("mock_body", "mock_signature")
    mock_process_message_event.assert_called_once_with(mock_event, mock_line_bot_api)
    assert response == "OK"


def test_main_invalid_signature_error(mock_cfg, mock_request, mock_parser):
    # Mock the parse method to raise InvalidSignatureError
    mock_parser.parse.side_effect = InvalidSignatureError

    # Check if RuntimeError is raised
    with pytest.raises(RuntimeError):
        main(mock_request)
