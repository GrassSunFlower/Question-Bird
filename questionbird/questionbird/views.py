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
			response = "Login Page is ready<a href='questionbird.sinaapp.com/login/?mmaname=%s'>click here</a>" %user.mmname
			user.last_oper = 0
		elif content == '2':
			response = "Register Page is ready<a href='questionbird.sinaapp.com/register/?mmaname=%s'>click here</a>" %user.mmname
			user.last_oper = 0
		elif content == '3':
			response = "Logout Page is ready<a href='questionbird.sinaapp.com/login/?mmaname=%s'>click here</a>" %user.mmname
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
	#登陆注册等事件
	if eventKey == E_KEY_LOGIN:
		login = "<a href='http://questionbird.sinaapp.com/login/?mmname=%s'>Login</a>" %user.mmname
		register = "<a href='http://questionbird.sinaapp.com/register/?mmname=%s'>Register</a>" %user.mmname
		logout = "<a href='http://questionbird.sinaapp.com/login/?mmname=%s'>Logout</a>" %user.mmname
		response = "Please Click:\n 1:%s\n 2:%s\n 3:%s" %(login, register, logout)
		user.last_oper = 0
	elif eventKey == E_KEY_SOLVED:
		response = "Solved Page Ready:<a href='http://questionbird.sinaapp.com/solved/?mmname=%s'>click here</a>" %user.mmname
		user.last_oper = 0
	else:
		#response = "Wrong Message Key!"
		exit(0)
	user.save()
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
	user = User.objects.filter(qbname='yo')
	if len(user) == 0:
		html = "<html><body><a href='www.baidu.com/?name=%s'>123</a></body></html>" % 'hahaha'
	else:
		html = "<html><body><a href='www.baidu.com/?name=%s'>123</a></body></html>" % user[0].password
	return HttpResponse(html)


def login(request):
	if request.method == "GET" and 'mmname' in request.GET:
		mmname_value = request.GET['mmname']
		return render_to_response('login.html', {'mmname':mmname_value})
	else:
		html = "<html><body>None</body></html>"
		return HttpResponse(html)

def solved(request):
	if request.method == "GET" and 'mmname' in request.GET:
		mmname = request.GET['mmname']
		userlist = User.objects.filter(mmname=mmname)
		qbname = userlist[0].qbname
		qbuserlist = QBUser.objects.filter(qbname=qbname)
		if len(qbuserlist) != 0:
			questionlist = Question.objects.filter(ques_owner=qbname, question_state="已解决")
			return render_to_response('questionsolvedlist.html', {'qbname':qbname,'questions':questionlist})
		else:
			html = "<html><body>请登录！</body></html>"
			return HttpResponse(html)
	else:
		html = "<html><body>请登录！</body></html>"
		return HttpResponse(html)


def unsolved(request):
	return render_to_response('questiontobesolvelist.html')


def register(request):
	if request.method == "GET" and 'mmname' in request.GET:
		mmname = request.GET['mmname']
		return render_to_response('register.html', {'mmname':mmname})
	elif request.method == "POST" and 'mmname' in request.POST:
		mmname = request.POST['mmname']
		qbname = request.POST['name']
		password = request.POST['password']
		qbuserlist = QBUser.objects.filter(qbname=qbname)
		if len(qbuserlist) == 0:
			qbuser = QBUser(qbname=qbname, password=password)
			qbuser.save()
			userlist = User.objects.filter(mmname=mmname)
			user = userlist[0]
			user.qbname = request.POST['name']
			user.password = request.POST['password']
			user.last_oper = 0
			user.save()
			helloword = "Register successfully and login automatically.Hello, %s!" % qbname
			html = "<html><body>%s</body></html>" % helloword
			return HttpResponse(html)
		else:
			return render_to_response('register.html', {'mmname':mmname})
	else:
		if request.method == "POST":
			for key in request.POST:
				print key
		html = "<html><body>None</body></html>"
		return HttpResponse(html)


def loginform(request):
	if request.method == "POST" and 'mmname' in request.POST:
		mmname= request.POST['mmname']
		userlist = User.objects.filter(mmname=mmname)
		user = userlist[0]
		user.qbname = request.POST['name']
		user.password = request.POST['password']
		user.last_oper = 0
		user.save()
		helloword = "welcome to QuestionBird, %s!" % user.qbname
		html = "<html><body>%s</body></html>" % helloword
		return HttpResponse(html)
	else:
		html = "<html><body>None</body></html>"
		return HttpResponse(html)
	
def index(request):
	helloword = "welcome to QuestionBird!"
	html = "<html><body>%s</body></html>" % helloword
	return HttpResponse(html)