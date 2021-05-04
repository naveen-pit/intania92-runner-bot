# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys
import redis
import datetime
from decimal import Decimal
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom,
)

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
REDIS_URI= os.getenv('REDIS_URI',None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)
if REDIS_URI is None:
    print('Specify REDIS_URI as environment variable.')
    sys.exit(1)
line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)
def get_current_month():
    return datetime.datetime.now().strftime('%B %Y')
def is_change_month(month_string):
    return get_current_month() != month_string.strip()
def parse_stats(message_list,user=None,increase_distance=Decimal('0')):
    sorted_list = []
    match_name = False
    if len(message_list) <2:
        return 'Please set title and subtitle'
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

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

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
        if messages[0:3]=='===':
            message_list = messages.split("\n")
            return_message = parse_stats(message_list)
        elif messages == '===get_time':
            return_message = datetime.datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)")
        elif "+" in messages:
            elements = messages.split("+")
            if len(elements)==2:
                name = elements[0].strip()
                if name.__contains__(' '):
                    return_message = "name cannot contain space"
                else:
                    distance = elements[1].strip()
                    try:
                        distance = Decimal(distance)
                    except ValueError:
                        return "OK"
                    r = redis.from_url(REDIS_URI)
                    stats = r.get(chat_id)

                    if stats is None:
                        return_message = "leaderboard not init"
                    else:
                        stats = str(stats,"utf-8")
                        message_list = stats.split("\n")
                        if message_list[0] == '===92 Running Challenge===': #automatically reset board for 92 Running Challenge 
                            if is_change_month(message_list[1]):
                                message_list = message_list[:2]
                                message_list[1] = get_current_month()
                        return_message = parse_stats(message_list,user=name,increase_distance=distance)
        if return_message:
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=return_message)
            )
            if return_message[0:3]=='===':
                print(return_message)
                r = redis.from_url(REDIS_URI)
                r.set(chat_id, return_message)
    return 'OK'


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0',port = port)
