"""Main entry point of a project."""

import io
from decimal import Decimal, InvalidOperation
from typing import Literal, Optional

import functions_framework
from flask import Flask, Request
from flask import request as req
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import Event,ImageMessage, MessageEvent, SourceGroup, SourceRoom, TextMessage, TextSendMessage
from PIL import Image
from running_bot.ocr import get_distance_easyocr

from .cloud_interface import get_leaderboard, get_name, set_leaderboard, set_name
from .config import cfg
from .google_cloud import Firestore
from .utils import get_current_month, is_change_month, is_valid_month_string

def is_leaderboard_format(text: str) -> bool:
    return text.startswith("===")


def parse_stats(message_list: list[str], user: str | None = None, increase_distance: Decimal = Decimal("0")) -> str:
    skip_rows=2
    if len(message_list) < skip_rows:
        return "Please set title and subtitle in the following format\n===TITLE \n SUBTITLE"
    
    sorted_list = []
    match_name = False
    for message in message_list[2:]:
        elements = message.strip().split(" ")
        name = elements[1].strip()
        try:
            distance = Decimal(elements[2])
        except InvalidOperation:
            return "Parse distance error, distance format is incorrect."
        if name == user:
            distance += increase_distance
            match_name = True
        elements[2] = str(distance)
        new_text = " ".join(elements[1:])
        if distance > 0:
            sorted_list.append((distance, new_text))
    if user and not match_name and increase_distance > 0:
        sorted_list.append((increase_distance, f"{user} {increase_distance} km"))
    sorted_list.sort(key=lambda x: x[0], reverse=True)
    
    return_message = "\n".join([message_list[0], message_list[1]] + 
                               [f"{idx + 1} {value[1]}" for idx, value in enumerate(sorted_list)])
    return return_message.strip()


def handle_leaderboard_update(messages: str, event: MessageEvent) -> str:
    message_list = messages.split("\n")
    return_message = parse_stats(message_list)
    if is_leaderboard_format(return_message):
        firestore_client = Firestore(project=cfg.project_id, database=cfg.firestore_database)
        set_leaderboard(firestore_client, chat_id=get_chat_id(event), value={"stats": return_message})
    return return_message


def update_distance_in_database(name: str, distance_string: str, chat_id: str, symbol: Literal["+", "-"]) -> str | None:
    elements = distance_string.split(symbol)
    if not elements:
        return "Invalid format"
    
    # Sum up all the distances
    total_distance = Decimal(0)
    
    try:
        total_distance = sum(Decimal(distance.strip()) for distance in elements)
    except InvalidOperation:
        return "Error parsing distance"
    
    if symbol == "-":
        total_distance = -total_distance
    
    if total_distance == Decimal(0):
        return None

    firestore_client = Firestore(project=cfg.project_id, database=cfg.firestore_database)
    leaderboard = get_leaderboard(firestore_client, chat_id)

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
    if isinstance(event.source, SourceGroup):
        return event.source.group_id
    elif isinstance(event.source, SourceRoom):
        return event.source.room_id
    return event.source.user_id



def process_message_event(event: MessageEvent, line_bot_api: LineBotApi) -> str | None:
    reply_message_list=[]
    return_message = None
    
    firestore_client = Firestore(project=cfg.project_id, database=cfg.firestore_database)
    stored_name = get_name(firestore_client, event.source.user_id)
    
    if isinstance(event.message, ImageMessage) and event.message.image_set is None and stored_name:
        return_message = handle_image_message(event, line_bot_api, stored_name, reply_message_list)
    elif isinstance(event.message, TextMessage):
        return_message = handle_text_message(event,stored_name, reply_message_list)
    if return_message:
        reply_message_list.append(TextSendMessage(text=return_message))
        line_bot_api.reply_message(event.reply_token, reply_message_list)
    
    return return_message  
    
def handle_image_message(event: MessageEvent, line_bot_api: LineBotApi, stored_name: dict, reply_message_list: list[TextSendMessage]) -> Optional[str]:
    name = stored_name["name"]
    message_content = line_bot_api.get_message_content(event.message.id)
    image = Image.open(io.BytesIO(message_content.content))
    distance = get_distance_easyocr(image)
    
    if distance > 0:
        update_message = f"{name} + {distance}"
        reply_message_list.append(TextSendMessage(text=update_message))
        return handle_distance_update(update_message, event,stored_name, reply_message_list, "+")
    return None

def handle_text_message(event: MessageEvent, stored_name: Optional[dict],reply_message_list: list) -> Optional[str]:
    messages = event.message.text.strip()
    if is_leaderboard_format(messages):
        return handle_leaderboard_update(messages, event)
    elif "+" in messages:
        return handle_distance_update(messages, event,stored_name, reply_message_list, "+")
    elif "-" in messages:
        return handle_distance_update(messages, event,stored_name, reply_message_list, "-")
    return None

def handle_distance_update(messages: str, event: MessageEvent,stored_name:Optional[dict],reply_message_list:list[TextSendMessage], split_symbol: Literal["+", "-"]) -> str | None:
    extracted_name, extracted_distance = extract_name_and_distance_from_message(messages, split_symbol)
    if not extracted_name or not extracted_distance:
        return "Name contains space or has invalid format"
    
    if stored_name is None or stored_name["name"] != extracted_name:
        firestore_client = Firestore(project=cfg.project_id, database=cfg.firestore_database)
        set_name(firestore_client, event.source.user_id, name=extracted_name)
        reply_message_list.append(TextSendMessage(text=f"Your name is set to {extracted_name}\nBot always uses your latest submitted name. To change your name, type 'Name+0'"))
    
    return update_distance_in_database(extracted_name, extracted_distance, get_chat_id(event), split_symbol)


def extract_name_and_distance_from_message(
    messages: str, split_symbol: Literal["+", "-"]
) -> tuple[str | None, str | None]:
    elements = messages.split(split_symbol, 1)
    valid_length = 2
    if len(elements) != valid_length or not elements[0].strip() or " " in elements[0].strip():
        return None, None
    return elements[0].strip(), elements[1]


@functions_framework.http
def reply(request: Request) -> str:
    main(request)
    return "OK"


def main(request: Request) -> str | None:
    channel_secret = cfg.line_channel_secret_key.get_secret_value()
    channel_access_token = cfg.line_access_token.get_secret_value()
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
        if isinstance(event, MessageEvent):
            process_message_event(event, line_bot_api)

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
