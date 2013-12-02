#! /usr/bin/env python
# coding=utf-8
__author__ = 'ypxtq'

from django.shortcuts import render
import hashlib
import xml.etree.ElementTree as ET
import urllib2
import time
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import datetime
from django.utils.encoding import smart_str, smart_unicode

# Create your views here.
@csrf_exempt
def handleRequest(request):
    if request.method == 'GET':
        #response = HttpResponse(request.GET['echostr'])
        response = HttpResponse(checkSignature(request),content_type="text/plain")
        return response
    if request.method == 'POST':
        #response = HttpResponse(response_msg(request),content_type="application/xml")
        response = HttpResponse(response_msg(request))
        #response = HttpResponse(123)
        return response
    else:
        return None


def checkSignature(request):
    #check whether the token is valid
    token = "questionbird"
    signature = request.GET.get('signature', None)
    timestamp = request.GET.get('timestamp', None)
    nonce = request.GET.get('nonce', None)
    echostr = request.GET.get('echostr', None)

    tmpList = [token, timestamp, nonce]
    tmpList.sort()
    tmpstr = "%s%s%s" % tuple(tmpList)
    hashstr = hashlib.sha1(tmpstr).hexdigest()

    if hashstr == signature:
        return echostr
    else:
        return None


# 解析请求,拆解到一个字典里
def parse_msg(rootElem):
    msg = {}
    #if rootElem.tag == 'xml':
    for child in rootElem:
        msg[child.tag] = smart_str(child.text)
    return msg


def set_content():
    content = "lulululu"
    return content



def response_msg(request):
    # 从request中获取输入文本
    rawStr = smart_str(request.raw_post_data)
    # 将文本进行解析,得到请求的数据
    msg = parse_msg(ET.fromstring(rawStr))
    # 根据请求消息来处理内容返回
    query_str = msg.get("Content")
    # query_str = "hello"
    response_msg = ""
    # 使用简单的处理逻辑，有待扩展
    if query_str == "hi":
        response_msg = "yo, sb"
    else:
        response_msg = "please input hi hahahahahah"
    # 返回消息
    # 包括post_msg，和对应的 response_msg
    return pack_text_xml(msg, response_msg)
    #return response_msg


# 打包消息xml，作为返回    
def pack_text_xml(post_msg,response_msg):
    # f = post_msg['FromUserName']   
    # t = post_msg['FromUserName']   
    text_tpl = '''<xml>   
                <ToUserName><![CDATA[%s]]></ToUserName>
                <FromUserName><![CDATA[%s]]></FromUserName>
                <CreateTime>%s</CreateTime>
                <MsgType><![CDATA[%s]]></MsgType>
                <Content><![CDATA[%s]]></Content>
                <FuncFlag>0</FuncFlag>
                </xml>'''   
    text_tpl = text_tpl % (post_msg['FromUserName'],post_msg['ToUserName'],str(int(time.time())),'text',response_msg)
    # 调换发送者和接收者，然后填入需要返回的信息到xml中
    return text_tpl

def test(request):
    now = datetime.datetime.now()
    html = "<html><body>It is now %s.</body></html>" % now
    return HttpResponse(html)


def index(request):
    helloword = "welcome to QuestionBird!"
    html = "<html><body>%s</body></html>" % helloword
    return HttpResponse(html)