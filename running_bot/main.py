"""Main entry point of a project."""

import io
from decimal import Decimal, InvalidOperation
from typing import Literal

import functions_framework
from flask import Flask, Request
from flask import request as req
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import ImageMessage, MessageEvent, SourceGroup, SourceRoom, TextMessage, TextSendMessage
from PIL import Image

from running_bot.ocr import get_distance_easyocr

from .cloud_interface import get_leaderboard, get_name, set_leaderboard, set_name
from .config import cfg
from .google_cloud import Firestore
from .utils import get_current_month, is_change_month, is_valid_month_string

channel_secret = cfg.line_channel_secret_key.get_secret_value()
channel_access_token = cfg.line_access_token.get_secret_value()
line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)


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
            print(name)
            print(distance)
        except InvalidOperation:
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


def handle_leaderboard_update(messages: str, event: MessageEvent) -> str:
    message_list = messages.split("\n")
    return_message = parse_stats(message_list)
    if return_message[0:3] == "===":
        firestore_client = Firestore(project=cfg.project_id, database=cfg.firestore_database)
        set_leaderboard(firestore_client, chat_id=get_chat_id(event), value={"stats": return_message})
    return return_message


def update_distance_in_database(name: str, distance_string: str, chat_id: str, symbol: Literal["+", "-"]) -> str | None:
    print("update distance in db")
    print("params")
    print(f"name:{name}")
    print(f"distance_string:{distance_string}")
    print(f"chat_id:{chat_id}")
    print(f"symbol:{symbol}")
    elements = distance_string.split(symbol)
    element_count = 1
    print(elements)
    if len(elements) < element_count:
        return "Invalid format"
    if len(elements) == element_count and elements[0] == 0:
        return None
    # Sum up all the distances
    total_distance = Decimal(0)
    for distance in elements:
        try:
            parsed_distance = Decimal(distance.strip())
            total_distance += parsed_distance
        except InvalidOperation:
            return f"Error parsing distance: {distance.strip()}"
    if symbol == "-":
        total_distance = -total_distance
    if total_distance==Decimal(0):
        return None
    print(f"total_distance={total_distance}")
    firestore_client = Firestore(project=cfg.project_id, database=cfg.firestore_database)
    leaderboard = get_leaderboard(firestore_client, chat_id)
    print(f"current_leaderboard: {leaderboard}")
    if leaderboard is None or "stats" not in leaderboard:
        message_list = ["===Running Challenge===", get_current_month()]
    else:
        stats = leaderboard["stats"]
        message_list = stats.split("\n")
        if is_valid_month_string(message_list[1]) and is_change_month(message_list[1]):
            message_list = message_list[:2]
            message_list[1] = get_current_month()

    return_message = parse_stats(message_list, user=name, increase_distance=total_distance)
    set_leaderboard(firestore_client, chat_id=chat_id, value={"stats": return_message})
    return return_message


def get_chat_id(event: MessageEvent) -> str:
    return (
        event.source.group_id
        if isinstance(event.source, SourceGroup)
        else event.source.room_id
        if isinstance(event.source, SourceRoom)
        else event.source.user_id
    )


def get_user_id(event: MessageEvent) -> str:
    return event.source.user_id


def process_event(event: MessageEvent, line_bot_api: LineBotApi) -> str | None:
    if isinstance(event, MessageEvent):
        return_message = None
        reply_message_list=[]
        reply_token = event.reply_token

        firestore_client = Firestore(project=cfg.project_id, database=cfg.firestore_database)

        stored_name = get_name(firestore_client, get_user_id(event))
        
        print(stored_name)
        print(event.message)
        print(isinstance(event.message, ImageMessage))
        # print("imageSet" not in event.message)
        # print(isinstance(event.message, ImageMessage) and "imageSet" not in event.message and stored_name)
        if isinstance(event.message, ImageMessage) and event.message.image_set is None and stored_name:
            name=stored_name["name"]
            message_id = event.message.id
            message_content = line_bot_api.get_message_content(message_id)
            print("got message content")
            # Read the image content into memory
            image_bytes = io.BytesIO(message_content.content)

            # Open the image using PIL
            image = Image.open(image_bytes)

            distance = get_distance_easyocr(image)
            print(distance)
            if distance > 0:
                update_message = f"{name} + {distance}"
                reply_message_list.append(TextSendMessage(text=update_message))
                return_message = handle_distance_update(update_message, event, "+")
                print("updated leaderboard in db")
                print(return_message)

        elif isinstance(event.message, TextMessage):
            messages = event.message.text.strip()
            if is_leaderboard_input(messages):
                return_message = handle_leaderboard_update(messages, event)
            elif "+" in messages:
                return_message = handle_distance_update(messages, event, "+")
            elif "-" in messages:
                return_message = handle_distance_update(messages, event, "-")
        print(return_message)
        if return_message:
            print("reply with leaderboard")
            # line_bot_api.push_message(get_chat_id(event),TextSendMessage(text=return_message))
            reply_message_list.append(TextSendMessage(text=return_message))
            line_bot_api.reply_message(reply_token,reply_message_list )
            return return_message
    return None


def handle_distance_update(messages: str, event: MessageEvent, split_symbol: Literal["+", "-"]) -> str | None:
    print("===handle distance update===")
    return_message = None
    extracted_name, extracted_distance = extract_name_and_distance_from_message(messages, split_symbol)
    print(extracted_name)
    print(extracted_distance)
    if extracted_name and extracted_distance:
        firestore_client = Firestore(project=cfg.project_id, database=cfg.firestore_database)
        # TODO(Naveen): send a message if extracted name and stored name does not match
        set_name(firestore_client, get_user_id(event), name=extracted_name)
        return_message = update_distance_in_database(
            extracted_name, extracted_distance, get_chat_id(event), split_symbol
        )
    else:
        return_message = "Name contains space or has invalid format"
    return return_message


def extract_name_and_distance_from_message(
    messages: str, split_symbol: Literal["+", "-"]
) -> tuple[str | None, str | None]:
    elements = messages.split(split_symbol, 1)
    name = elements[0].strip()
    valid_length = 2
    if name == "" or " " in name or len(elements) < valid_length:
        return None, None
    return name, elements[1]


@functions_framework.http
def reply(request: Request) -> str:
    main(request)
    return "OK"


def main(request: Request) -> str | None:
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
    print("callback")
    main(req)
    print("done")
    return "OK"
