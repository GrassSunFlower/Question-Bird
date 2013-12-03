#! /usr/bin/env python
# coding=utf-8
__author__ = 'ypxtq'


import hashlib,urllib2
import xml.etree.ElementTree as ET
import time,json,datetime
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import smart_str, smart_unicode
from questionbird.keys import *
from questionbird.models import *
from django.shortcuts import *
from django.template import *

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
		return response
	else:
		return None


def checkSignature(request):
	#check whether the token is valid
	token = QB_TOKEN
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
	if rootElem.tag == 'xml':
		for child in rootElem:
			msg[child.tag] = smart_str(child.text)
	return msg


def set_content():
	content = "lulululu"
	return content


def create_user(mmname):
	user = User(mmname=mmname,qbname='',password='',last_oper=0)
	user.save()


def response_msg(request):
	# 从request中获取输入文本
	rawStr = smart_str(request.raw_post_data)
	# 将文本进行解析,得到请求的数据
	msg = parse_msg(ET.fromstring(rawStr))
	mmname = msg["FromUserName"]
	user = User.objects.filter(mmname=mmname)
	if len(user) == 0:
		create_user(mmname)
        user = User.objects.filter(mmname=mmname)
	response_msg = ""
	#message_type = msg.get("MsgType")
	message_type = msg["MsgType"]
	#处理文本消息
	if message_type == "text":
		response_msg = handle_text(msg, user[0])
	#处理事件消息
	elif message_type == "event":
		response_msg = handle_event(msg, user[0])
	else:
		response_msg = 'Wrong Message Type!'
	# 返回消息
	return pack_text_xml(msg, response_msg)


def handle_text(msg, user):
	content = msg.get("Content")
	response = ""
	if user.last_oper == 100:
		if content == '1':
			response = "登陆页面已为您准备好，请点击<a href='questionbird.sinaapp.com/login'>这里</a>"
			user.last_oper = 0
		elif content == '2':
			response = "注册页面已为您准备好，请点击<a href='questionbird.sinaapp.com/register'>这里</a>"
			user.last_oper = 0
		elif content == '3':
			response = "登出页面已为您准备好，请点击<a href='questionbird.sinaapp.com/login'>这里</a>"
			user.last_oper = 0
		else:
			response = "无效命令，请重新输入："
			user.last_oper = 100
		user.save()
	else:
		if content == "hi":
			response = "yo, sb"
		else:
			response = "please input hi hahahahahah"
	return response

def handle_event(msg, user):
	eventKey = msg.get("EventKey")
	response = ""
	#登陆注册等事件
	if eventKey == LOGIN:
		response = "请输入您要进行的操作:\n1:登陆\n2:注册\n3:登出"
		user.last_oper = 100
		user.save()
	else:
		#response = "Wrong Message Key!"
		exit(0)
	return response
# 打包消息xml，作为返回    
def pack_text_xml(post_msg,response_msg):
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
	user = User.objects.filter(qbname='yo111')
	if len(user) == 0:
		html = "<html><body>%s</body></html>" % 'hahaha'
	else:
		html = "<html><body>%s</body></html>" % user[0].password
	return HttpResponse(html)


def login(request):
	return render_to_response('login.html')


def solved(request):
	return render_to_response('questionsolvedlist.html')


def unsolved(request):
	return render_to_response('questiontobesolvelist.html')


def register(request):
	return render_to_response('register.html')

	
def index(request):
	helloword = "welcome to QuestionBird!"
	html = "<html><body>%s</body></html>" % helloword
	return HttpResponse(html)