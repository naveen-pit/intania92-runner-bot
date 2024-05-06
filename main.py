"""Main entry point of a project."""
import functions_framework
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
)

from inputs import get_line_credentials


@functions_framework.http
def reply(request) -> None:  # noqa: ANN001
    main(request)


def main(request) -> None:  # noqa: ANN001
    channel_secret, channel_access_token = get_line_credentials()

    line_bot_api = LineBotApi(channel_access_token)
    parser = WebhookParser(channel_secret)

    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        raise RuntimeError from None

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        messages = event.message.text
        messages = messages.strip()
        reply_token = event.reply_token
        return_message = messages
        line_bot_api.reply_message(reply_token, TextSendMessage(text=return_message))
