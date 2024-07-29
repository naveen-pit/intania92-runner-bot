"""Main entry point of a project."""

from decimal import Decimal

import functions_framework
from flask import Flask, Request
from flask import request as req
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    SourceGroup,
    SourceRoom,
    TextMessage,
    TextSendMessage,
)

from cloud_interface import get_leaderboard, get_line_credentials, set_leaderboard
from constants import FIRESTORE_DATABASE, PROJECT_ID
from google_cloud import Firestore
from utils import get_current_month, is_change_month


def is_leaderboard_input(text: str) -> bool:
    return text[0:3] == "==="


def parse_stats(message_list: list[str], user: str | None = None, increase_distance: Decimal = Decimal("0")) -> str:
    sorted_list = []
    match_name = False
    skip_rows = 2
    if len(message_list) < skip_rows:
        return "Please set title and subtitle in the following format\n===TITLE \n SUBTITLE"
    for i in range(2, len(message_list)):
        message = message_list[i]
        elements = message.strip().split(" ")
        name = elements[1].strip()
        distance = Decimal(0.0)
        try:
            distance = Decimal(elements[2])
        except ValueError:
            return "Parse distance error, distance format is incorrect."
        if name == user:
            distance = distance + increase_distance
            match_name = True
        elements[2] = str(distance)
        new_text = " ".join(elements[1:])
        if distance > 0:
            sorted_list.append((distance, new_text))
    if user and not match_name and increase_distance > 0:
        sorted_list.append((increase_distance, user + " " + str(increase_distance) + " km"))
    sorted_list.sort(key=lambda x: x[0], reverse=True)
    return_message = message_list[0] + "\n" + message_list[1] + "\n"
    for idx, value in enumerate(sorted_list):
        return_message = return_message + str(idx + 1) + " " + value[1] + "\n"
    return_message = return_message.strip()
    return return_message


def handle_leaderboard_update(messages: str, chat_id: str) -> str:
    message_list = messages.split("\n")
    return_message = parse_stats(message_list)
    if return_message[0:3] == "===":
        firestore_client = Firestore(project=PROJECT_ID, database=FIRESTORE_DATABASE)
        set_leaderboard(firestore_client, chat_id=chat_id, value={"stats": return_message})
    return return_message


def handle_distance_update(messages: str, chat_id: str) -> str:
    elements = messages.split("+")
    element_count = 2
    if len(elements) != element_count:
        return "Invalid format"

    name = elements[0].strip()
    if " " in name:
        return "Name cannot contain space"

    distance = elements[1].strip()
    try:
        parsed_distance = Decimal(distance)
    except ValueError:
        return "Error parsing distance"
    firestore_client = Firestore(project=PROJECT_ID, database=FIRESTORE_DATABASE)
    leaderboard = get_leaderboard(firestore_client, chat_id)
    if leaderboard is None or "stats" not in leaderboard:
        return "Leaderboard not initialized"

    stats = leaderboard["stats"]
    message_list = stats.split("\n")
    if message_list[0] == "===92 Running Challenge===" and is_change_month(message_list[1]):
        message_list = message_list[:2]
        message_list[1] = get_current_month()

    return_message = parse_stats(message_list, user=name, increase_distance=parsed_distance)
    set_leaderboard(firestore_client, chat_id=chat_id, value={"stats": return_message})
    return return_message


def process_event(event: MessageEvent, line_bot_api: LineBotApi) -> str | None:
    if not isinstance(event, MessageEvent) or not isinstance(event.message, TextMessage):
        return None

    chat_id = (
        event.source.group_id
        if isinstance(event.source, SourceGroup)
        else event.source.room_id
        if isinstance(event.source, SourceRoom)
        else event.source.user_id
    )

    messages = event.message.text.strip()
    reply_token = event.reply_token
    return_message = None

    if is_leaderboard_input(messages):
        return_message = handle_leaderboard_update(messages, chat_id)
    elif "+" in messages:
        return_message = handle_distance_update(messages, chat_id)
    if return_message:
        line_bot_api.reply_message(reply_token, TextSendMessage(text=return_message))
    return return_message


@functions_framework.http
def reply(request: Request) -> str:
    main(request)
    return "OK"


def main(request: Request) -> str | None:
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
        process_event(event, line_bot_api)

    return "OK"


app = Flask(__name__)


@app.route("/", methods=["GET"])
def home() -> str:
    return "LINE BOT HOME"


@app.route("/", methods=["POST"])
def callback() -> str:
    main(req)
    return "OK"
