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
import re
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
        message_list = messages.split("\n")
        
        if message_list[0].strip()[0:3]=='===':
            sorted_list = []
            for i in range(2,len(message_list)):
                message = message_list[i]
                elements = message.strip().split(" ")
                distance = re.sub(r"[^0-9.]","",elements[2]).strip()
                try:
                    distance = float(distance)
                except ValueError:
                    distance = 0
                sorted_list.append((distance,i))
            sorted_list.sort(key=lambda x:x[0],reverse=True)
            return_message = message_list[0]+"\n"+message_list[1]+"\n"
            for info in sorted_list:
                return_message = return_message+message_list[info[1]]+"\n"
            return_message = return_message.strip()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=return_message)
            )
        # elif message_list[0][0]=="+":
        #     message = message_list[0][1:]
        #     elements = message.strip().split(" ")
        #     name = elements[0]
        #     distance = elements[1]


    return 'OK'


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0',port = port)
