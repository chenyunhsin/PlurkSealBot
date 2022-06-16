#!/usr/bin/python
# -*- coding:utf-8 -*-
from datetime import datetime
from datetime import timedelta

import random
import numpy as np
import requests
import re
import json
import urllib.request
from quickdraw import QuickDrawData

import pyimgur
import time
from plurk_oauth import PlurkAPI
from twoLight import twoLight
from gue import gue
from gua import check_gua
from eddecode import encode, decode
from palindromic5 import longestPalindrome
from sealDB import *

google_key = ""
client_id = ''
client_secret = ''



random_list = ["udemy的瑜珈課好讚", "今天過得開心嗎(p-rock)", "終於通過檢定,拿到180星了！", "讚讚 [emo10]",
               "我的種蔥好像掛了:(", "棒棒地[emo9]", "我的可愛要過期了完結了[emo20]"
    , "加了杏鮑菇切碎加五香粉,就是漢堡肉的味道了:0", "炸地瓜球好好吃喔0.0", "哺嚕哺嚕貓[emo8]", "還是要小心疫情喔[emo2]", "期待中秋節獎金[emo9] ",
               "巴拉巴拉巴拉噗噗噗噗嚕嚕噗嚕噗噗噗～～", "最近azure有辦活動,達成成就可以免費考證照喔[emo8] https://www.microsoft.com/en-US/cloudskillschallenge/build/registration/2022?fbclid=IwAR1XVrAM4_zub-cVUHNy4LVyl7FJDWEWsR2ippzY8ALCTVOFxXk6fybuqzw",
               "要多肯定自己的努力喔[emo9]", "玫瑰鹽焦糖巧克力口味的曠世奇派超好吃！"]
headers = {'x-api-key': ''}
plurk = PlurkAPI('', '')
plurk.authorize('', '')
comet = plurk.callAPI('/APP/Realtime/getUserChannel')
comet_channel = comet.get('comet_server') + "&new_offset=%d"
jsonp_re = re.compile('CometChannel.scriptCallback\((.+)\);\s*');


def auth():
    plurk.authorize('', '')
    time.sleep(0.1)
    comet = plurk.callAPI('/APP/Realtime/getUserChannel')
    try:
        comet_channel = comet.get('comet_server') + "&new_offset=%d"
        jsonp_re = re.compile('CometChannel.scriptCallback\((.+)\);\s*');
    except Exception as e:
        print("[err]auth:")
        print(e)
    # print("auth ok!")


def setFriendList():
    try:
        data = plurk.callAPI('/APP/FriendsFans/getCompletion')
        # data=plurk.callAPI('/APP/FriendsFans/getFriendsByOffset',{'user_id':'16297121','limit':99999})
        time.sleep(0.1)
        if data is not None:
            for user in data:
                if not user in friend_list:
                    friend_list.append(user)
        print("friend list:" + str(len(friend_list)))

    except Exception as e:
        print("setFriendList err:")
        print(e)


def printTime():
    now = datetime.now()
    print("time:" + now.strftime("%d/%m/%Y %H:%M:%S"))


def initApi():
    auth()
    plurk.callAPI('/APP/Alerts/addAllAsFriends')
    time.sleep(0.1)
    setFriendList()
    # print("init:"+str(new_offset))
    req = urllib.request.urlopen(comet_channel % new_offset, timeout=80)
    time.sleep(0.1)
    rawdata = req.read()
    match = jsonp_re.match(rawdata.decode('ISO-8859-1'))
    return match




def plurkResponse(pid, content):
    x = plurk.callAPI('/APP/Responses/responseAdd', {'plurk_id': pid,
                                                     'content': content, 'qualifier': ':'})

    # print("response err pid:"+str(pid)+"content:"+str(content)+str(x))
    time.sleep(0.1)


def plurkAdd(user_id, content):
    x = plurk.callAPI('/APP/Timeline/plurkAdd', {'content': content, 'qualifier': ':', 'limited_to': [user_id]})
    time.sleep(0.1)


def getPlurks():
    plurks = plurk.callAPI('/APP/Polling/getPlurks')
    time.sleep(0.1)
    print("polling plurks:")
    print(plurks)


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
                        if checkIsGuessing(pu['from_user']['id'], pu['plurk_id']):
                            print("guessing game plurk" + str(guess_game))
                            isBingo_v = isBingo(target, pu['plurk_id'])
                            if isBingo_v:
                                bingoGuessGame(pu['plurk_id'])
                            elif target.find("窩不知道") != -1:
                                endGuessGame(pu['plurk_id'])
                            else:
                                seal_num = random.randint(1, 5)
                                if seal_num == 1:
                                    plurkResponse(pu['plurk_id'], '不對～再猜猜～')
                                elif seal_num == 2:
                                    plurkResponse(pu['plurk_id'], '不對喔～再猜猜看～')
                                elif seal_num == 3:
                                    plurkResponse(pu['plurk_id'], '加油～再試試～')
                                elif seal_num == 4:
                                    plurkResponse(pu['plurk_id'], '是英文喔0.0')
                                elif seal_num == 5:
                                    plurkResponse(pu['plurk_id'], '可以參考quick draw喔～～')
                        else:
                            print("**mentioned by:" + str(pu))
                            dealContent(pid, target, True, pu, pu['from_user']['id'])



print("Seal bot is working!")





def dealContent(pid, content, isCmd, pu, user_id):
    print("reply plurk id:" + str(pid) + " content:" + content + " pu:" + str(pu))
    if content.find("進村") != -1 or content.find("開村") != -1:
        plurkResponse(pid, '真麻煩（＃ 進村拉～[emo2]')
        time.sleep(1)
    if content.find("台灣新聞") != -1:
        response = requests.get(news_url)
        print(response.json())
        if response.status_code == 200:
            articles = response.json()['articles']
            for art in articles:
                if art is not None:
                    plurkResponse(pid, "標題：" + art['title'])
                    if art['description'] is not None:
                        print("***")
                        print(art['description'])
                        plurkResponse(pid, "內容擷取：" + art['description'])
                        time.sleep(1)
                    if art['url'] is not None:
                        plurkResponse(pid, "新聞連結：" + art['url'])
                        time.sleep(1)
            plurkResponse(pid, "以上～")

        else:
            plurkResponse(pid, '沒有新聞耶:0')
    if content.find("鴨鴨") != -1:
        response = requests.get(duck_url)
        if response.status_code == 200:
            plurkResponse(pid, '呱呱！' + response.json()['url'])
    else:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        x = current_time.split(":")
        h = x[0]
        if content.find("謝謝") != -1:
            plurkResponse(pid, "不客氣！[emo9]")
        elif content.find("喜歡") != -1 or content.find("棒") != -1:
            plurkResponse(pid, "謝謝你的喜歡！也記得要這麼喜歡自己喔！[emo9]")
        elif content.find("豹豹") != -1 and content.find("可愛") != -1:
            plurkResponse(pid, "你才可愛！你全家都可愛！[emo9]")
        elif content.find("我愛你") != -1:
            plurkResponse(pid, "窩也愛你！[emo9]")
        else:
            random.shuffle(random_list)
            plurkResponse(pid, random_list[0])

while True:
    printTime()
    match = initApi()
    checkEndGuessGame()
    if match:
        rawdata = match.group(1)
    data = json.loads(rawdata)

    new_offset = data.get('new_offset', -1)

    msgs = data.get('data')
    responseMentioned()

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
            print(f"Not in friend list. id:{user_id} {msg.get('content_raw')}")
            # print(str(friend_list))
            continue

        if msg.get('type') == 'new_plurk':
            print("reply now user:" + str(user_id) + " msg:" + str(msg.get('content')))
            content = msg.get('content_raw')
            if content.find("--noreply") != -1 or content.find("慎入") != -1:
                print(":p")
            else:
                dealContent(pid, content, False, "", user_id)
