"""Main entry point of a project."""
import os

import functions_framework
from flask import Flask
from flask import request as req
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
)

from inputs import get_line_credentials


@functions_framework.http
def reply(request) -> str:  # noqa: ANN001
    main(request)
    return "OK"


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


app = Flask(__name__)


@app.route("/", methods=["GET"])
def home() -> str:
    return "LINE BOT HOME"


@app.route("/callback", methods=["POST"])
def callback() -> str:
    main(req)
    return "OK"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
