import os
import redis
import re
URI="redis://h:p2683f9465e2fcbb6e728f84f905a3234994c14cc2be4e7bcff93c653b67a4480@ec2-35-168-215-149.compute-1.amazonaws.com:17159"
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
# messages = """===92 Running Challenge #7===
# (1Mar-30Apr)"""
messages = "New_user+8"
messages = messages.strip()
reply_token = "9292" #event.reply_token

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
            pass #return
        r = redis.from_url(URI)
        stats = r.get(reply_token)

        if stats is None:
            return_message = "leaderboard not init"
        else:
            stats = str(stats,"utf-8")
            return_message = parse_stats(stats,user=name,increase_distance=distance)
if return_message:
    # line_bot_api.reply_message(
    #     reply_token,
    #     TextSendMessage(text=return_message)
    # )
    if return_message[0:3]=='===':
        print(return_message)
        r = redis.from_url(URI)
        r.set(reply_token, return_message)