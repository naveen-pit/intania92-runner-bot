# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from __future__ import unicode_literals

import os
import sys
import redis
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
)

app = Flask(__name__)
URI="redis://h:p2683f9465e2fcbb6e728f84f905a3234994c14cc2be4e7bcff93c653b67a4480@ec2-35-168-215-149.compute-1.amazonaws.com:17159"
# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)

def parse_stats(stats,user=None,increase_distance=0):
    message_list = stats.split("\n")
    sorted_list = []
    match_name = False
    for i in range(2,len(message_list)):
        message = message_list[i]
        elements = message.strip().split(" ")
        name = elements[1].strip()
        distance = 0.0
        try:
            distance = float(elements[2])
        except ValueError:
            return "Parse distance error, distance format is incorrect."
        if name == user:
            distance = distance + increase_distance
            match_name = True
        elements[2] = str(distance)
        new_text = ' '.join(elements[1:])
        sorted_list.append((distance,new_text))
    if user and not match_name:
        sorted_list.append((increase_distance,user+" "+str(increase_distance)))
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
        messages = event.message.text
        messages = messages.strip()
        reply_token = event.reply_token

        return_message = None
        if messages[0:3]=='===':
            return_message = parse_stats(messages)

        elif "+" in messages:
            elements = messages.split("+")
            if len(elements)==2:
                name = elements[0].strip()
                distance = elements[1].strip()
                try:
                    distance = float(distance)
                except ValueError:
                    return "OK"
                r = redis.from_url(URI)
                stats = r.get(reply_token)

                if stats is None:
                    return_message = "leaderboard not init"
                else:
                    stats = str(stats,"utf-8")
                    return_message = parse_stats(stats,user=name,increase_distance=distance)
        if return_message:
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=return_message)
            )
            if return_message[0:3]=='===':
                print(return_message)
                r = redis.from_url(URI)
                r.set(reply_token, return_message)


    return 'OK'


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0',port = port)
