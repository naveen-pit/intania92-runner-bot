"""Main entry point of a project."""
from decimal import Decimal
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
    SourceUser, SourceGroup, SourceRoom,
)

from inputs import get_line_credentials
from utils import get_current_month, is_change_month

def is_leaderboard_input(text):
    return text[0:3]=='==='



def parse_stats(message_list,user=None,increase_distance=Decimal('0')):
    sorted_list = []
    match_name = False
    if len(message_list) <2:
        return 'Please set title and subtitle in the following format\n===TITLE \n SUBTITLE'
    for i in range(2,len(message_list)):
        message = message_list[i]
        elements = message.strip().split(" ")
        name = elements[1].strip()
        distance = 0.0
        try:
            distance = Decimal(elements[2])
        except ValueError:
            return "Parse distance error, distance format is incorrect."
        if name == user:
            distance = distance + increase_distance
            match_name = True
        elements[2] = str(distance)
        new_text = ' '.join(elements[1:])
        if distance > 0:
            sorted_list.append((distance,new_text))
    if user and not match_name and increase_distance>0:
        sorted_list.append((increase_distance,user+" "+str(increase_distance)+ " km"))
    sorted_list.sort(key=lambda x:x[0],reverse=True)
    return_message = message_list[0]+"\n"+message_list[1]+"\n"
    for idx,value in enumerate(sorted_list):
        return_message = return_message+str(idx+1)+" "+value[1]+"\n"
    return_message = return_message.strip()
    return return_message

@functions_framework.http
def reply(request) -> str:  # noqa: ANN001
    main(request)
    return "OK"


def main(request) -> None:  # noqa: ANN001
    channel_secret, channel_access_token = get_line_credentials()
    print("GOT CREDENTIAL")
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
        if isinstance(event.source, SourceGroup):
            chat_id = event.source.group_id
        elif isinstance(event.source, SourceRoom):
            chat_id = event.source.room_id
        else:
            chat_id = event.source.user_id

        messages = event.message.text
        messages = messages.strip()
        reply_token = event.reply_token
        return_message = None

        if is_leaderboard_input(messages):
            message_list = messages.split("\n")
            return_message = parse_stats(message_list)

        elif "+" in messages:
            elements = messages.split("+")
            print("+ in already")
            if len(elements)==2:
                name = elements[0].strip()
                print("name")
                print(name)
                if name.__contains__(' '):
                    return_message = "name cannot contain space"
                else:
                    distance = elements[1].strip()
                    print("distance")
                    print(distance)
                    try:
                        distance = Decimal(distance)
                    except ValueError:
                        return "Error parsing distance"
                    # r = redis.from_url(REDIS_URI)
                    # stats = r.get(chat_id)
                    # TODO temporary stats
                    stats = """===92 Running Challenge===\nJune 2024"""
                    print("stats")
                    print(stats)
                    if stats is None:
                        print("stats is None")
                        return_message = "leaderboard not init"
                    else:
                        # stats = str(stats,"utf-8")
                        message_list = stats.split("\n")
                        print("message_list")
                        print(message_list)
                        if message_list[0] == '===92 Running Challenge===': #automatically reset board for 92 Running Challenge 
                            if is_change_month(message_list[1]):
                                message_list = message_list[:2]
                                message_list[1] = get_current_month()
                        
                        return_message = parse_stats(message_list,user=name,increase_distance=distance)
        print("return_message")
        print(return_message)
        if return_message:
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=return_message)
            )
            if return_message[0:3]=='===':
                print(return_message)
                # r = redis.from_url(REDIS_URI)
                # r.set(chat_id, return_message)


app = Flask(__name__)


@app.route("/", methods=["GET"])
def home() -> str:
    return "LINE BOT HOME"


@app.route("/", methods=["POST"])
def callback() -> str:
    main(req)
    return "OK"

