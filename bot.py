import random
import requests
import re
import json
import urllib.request


import time
from plurk_oauth import PlurkAPI

# 以下請替換成自己的值！
friend_list = []
headers = {'x-api-key': '{$$.env.x-api-key}'}
plurk = PlurkAPI('APP_KEY', 'APP_SECRET')
plurk.authorize('ACCEESS_TOKEN', 'ACCESS_TOKEN_SECRET')

random_list = [ "今天過得開心嗎(p-rock)", "讚讚 [emo10]", "棒棒地[emo9]"]
comet = plurk.callAPI('/APP/Realtime/getUserChannel')
comet_channel = comet.get('comet_server') + "&new_offset=%d"
jsonp_re = re.compile('CometChannel.scriptCallback\((.+)\);\s*');
new_offset = -1

def auth():
    plurk.authorize('ACCEESS_TOKEN', 'ACCESS_TOKEN_SECRET')
    time.sleep(0.1)
    comet = plurk.callAPI('/APP/Realtime/getUserChannel')
    try:
        comet_channel = comet.get('comet_server') + "&new_offset=%d"
        jsonp_re = re.compile('CometChannel.scriptCallback\((.+)\);\s*');
    except Exception as e:
        print(f"[err]auth:{e}")


def setFriendList():
    try:
        data = plurk.callAPI('/APP/FriendsFans/getCompletion')
        if data is not None:
            for user in data:
                if not user in friend_list:
                    friend_list.append(user)
    except Exception as e:
        print(f"setFriendList err: {e}")

#回噗    
def plurkResponse(pid,content):
    plurk.callAPI('/APP/Responses/responseAdd', {'plurk_id': pid,
                                                 'content': content, 'qualifier': ':'})
def initApi():
    auth()
    plurk.callAPI('/APP/Alerts/addAllAsFriends')
    setFriendList()
    req = urllib.request.urlopen(comet_channel % new_offset, timeout=80)
    rawdata = req.read()
    match = jsonp_re.match(rawdata.decode('ISO-8859-1'))
    return match


def findTargetResponse(res_list, res_id):
    for res in res_list:
        if res['id'] == res_id:
            return res['content_raw']
    return "not found"


def responseMentioned():
    plurks = plurk.callAPI('/APP/Alerts/getActive')
    if plurks is not None:
        for pu in plurks:
            if pu is not None:
                if pu['type'] == "mentioned":
                    res_id = pu['response_id']
                    pid = pu['plurk_id']
                    res_json = plurk.callAPI('/APP/Responses/get', {'plurk_id': pid})
                    if res_json is None:
                        pass
                    else:
                        res_list = res_json['responses']
                        target = findTargetResponse(res_list, res_id)
                        dealContent(pid, target, True, pu, pu['from_user']['id'])


def dealContent(pid, content, isCmd, pu, user_id):
    print(f"reply plurk id:{pid} content:{content} pu: {pu}")
    if content.find("進村") != -1 or content.find("開村") != -1:
        plurkResponse(pid, ' 進村拉～')
    if content.find("鴨鴨") != -1:
        response = requests.get(duck_url)
        if response.status_code == 200:
            plurkResponse(pid, '呱呱！' + response.json()['url'])
    else:
        if content.find("謝謝") != -1:
            plurkResponse(pid, "不客氣拉！[emo9]")
        elif content.find("喜歡") != -1 or content.find("棒") != -1:
            plurkResponse(pid, "謝謝你的喜歡！也記得要這麼喜歡自己喔！[emo9]")
        else:
            random.shuffle(random_list)
            plurkResponse(pid, random_list[0])

            
while True:
    match = initApi()
    if match:
        rawdata = match.group(1)
    data = json.loads(rawdata)
    new_offset = data.get('new_offset', -1)
    msgs = data.get('data')
    responseMentioned()
    print("Seal bot is working!")
    if not msgs:
        continue
    for msg in msgs:
        pid = msg.get('plurk_id')
        user_id = msg.get('user_id')

        if user_id is None:
            try:
                pid = msg['plurk']['plurk_id']
                user_id = msg['plurk']['user_id']
            except Exception as e:
                print("sth wrong: msg:" + str(e))
                continue

        if str(user_id) not in friend_list:
            print("Not in friend list.")
            continue

        if msg.get('type') == 'new_plurk':
            print(f"reply now user:{user_id} msg: {msg.get('content')}")
            content = msg.get('content_raw')
            if content.find("--noreply") != -1 or content.find("慎入") != -1:
                print(":p")
            else:
                dealContent(pid, content, False, "", user_id)
