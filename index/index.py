#! /usr/bin/env python
# coding=utf-8
__author__ = 'ypxtq'
#using bottle here, a python web framework
from bottle import *
import hashlib
import xml.etree.ElementTree as ET
import urllib2
import json

app = Bottle()

@app.get("/")
def checkSignature():
    #check whether the token is valid
    token = "thuhelper" 
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

def parse_msg():
    #"parse the command sent from wechat"
    recvmsg = request.body.read()  
    root = ET.fromstring(recvmsg)
    msg = {}
    for child in root:
        msg[child.tag] = child.text
    return msg

def set_content():
    content = "sb"
    return content

@app.post("/")
def response_msg():
    msg = parse_msg()
    #handle text message
    textTpl = """<xml>
             <ToUserName><![CDATA[%s]]></ToUserName>
             <FromUserName><![CDATA[%s]]></FromUserName>
             <CreateTime>%s</CreateTime>
             <MsgType><![CDATA[text]]></MsgType>
             <Content><![CDATA[%s]]></Content>
             <FuncFlag>0</FuncFlag>
             </xml>"""
    locationTpl = """<xml>
             <ToUserName><![CDATA[%s]]></ToUserName>
             <FromUserName><![CDATA[%s]]></FromUserName>
             <CreateTime>%s</CreateTime>
             <MsgType><![CDATA[text]]></MsgType>
             <Location_X>23.134521</Location_X>
             <Location_Y>113.358803</Location_Y>
             <Scale>20</Scale>
             <Label><![CDATA[location]]></Label>
             <MsgId>1234567890123456></MsgId>
             </xml>"""
    content = set_content()
    if msg['Content'] == "hi":
      echostr = textTpl % (
                           msg['FromUserName'], msg['ToUserName'], str(int(time.time())),
<<<<<<< HEAD
                           content)
      return echostr
    elif msg['Content'] == "location":
      echostr = textTpl % (
                           msg['FromUserName'], msg['ToUserName'], str(int(time.time())),
                           )
      return echostr
 
=======
                           "回复001：使用info用户名和密码登录\n回复002：退出登录")
        return echostr
    elif msg['MsgType'] == "text" and msg['Content'] == "hi":
        echostr = textTpl % (
                           msg['FromUserName'], msg['ToUserName'], str(int(time.time())),
                           msg['FromUserName'] + " is a sb")
        return echostr
    else:
        echostr = textTpl % (
                           msg['FromUserName'], msg['ToUserName'], str(int(time.time())),
                           'please input hi')
        return echostr

>>>>>>> 2b4665ee9347ed070c7650d134a3db646749a4a4
#call bae serive
from bae.core.wsgi import WSGIApplication
#create application
application = WSGIApplication(app)