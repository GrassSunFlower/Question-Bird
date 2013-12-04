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
		return HttpResponse('看不到你看不到')


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
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			question = Question(
								ques_owner=user.qbname,content='',category='',
								question_state='已选科',answer='',answer_state='',
								answer_satis='',answer_eva='',solver_name='')
			if content in CATEGORY_DIC:
				question.category = CATEGORY_DIC[content]
				question.save()
				user.last_oper = 101
				response = '您的问题类型为:%s\n\r请输入您要提问的内容:' %question.category
			else:
				response = '无效的选项，请重新输入'
				user.last_oper = 100
	elif user.last_oper == 101:
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			questionlist = Question.objects.filter(ques_owner=user.qbname,question_state='已选科')
			if len(questionlist) == 0:
				response = "未知的错误!请重新点击'我要提问'按钮开始提问"
				user.last_oper = 0
			else:
				question = questionlist[0]
				question.content = content
				question.question_state = '待解决'
				user.last_oper = 0
				question.save()
				response = '提问成功，半小时内将有老师为您解答，请耐心等待~'
	else:
		if content == "hi":
			response = "yo, sb"
		else:
			response = "请点击下面的按钮选择相应的服务~"
		user.last_oper = 0
	user.save()
	return response


def handle_event(msg, user):
	eventKey = msg.get("EventKey")
	#登录注册等事件
	#未登录时可注册和登录
	if eventKey == E_KEY_LOGIN and len(user.qbname) == 0:
		login = "<a href='http://questionbird.sinaapp.com/login/?mmname=%s'>登录</a>" %user.mmname.encode('utf-8')
		register = "<a href='http://questionbird.sinaapp.com/register/?mmname=%s'>注册</a>" %user.mmname.encode('utf-8')
		response = "请选择需要的操作:\n\r%s     %s" %(login, register)
		user.last_oper = 0
	#已登录后只能登出
	elif eventKey == E_KEY_LOGIN:
		user.qbname = ''
		user.password = ''
		user.save()
		user.last_oper = 0
		response = '登出成功!'
	elif eventKey == E_KEY_ASK:
		#尚未登录
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			response = "请选择问题类型:\n\r1.小学语文\n\r2.小学数学\n\r3.初中语文\n\r4.初中数学\n\r5.初中英语\n\r6.高中语文\n\r7.高中数学\n\r8.高中英语"
			user.last_oper = 100
	elif eventKey == E_KEY_SOLVED:
		if len(user.qbname) == 0:
			response = '请先登录!'
			user.last_oper = 0
		else:
			response = "已解决问题的列表页面已为您准备好，请<a href='http://questionbird.sinaapp.com/solved/?mmname=%s'>点击</a>" %user.mmname.encode('utf-8')
			user.last_oper = 0
	elif eventKey == E_KEY_UNSOLVED:
		if len(user.qbname) == 0:
			response = '请先登录!'
			user.last_oper = 0
		else:
			response = "待解决问题的列表页面已为您准备好，请<a href='http://questionbird.sinaapp.com/unsolved/?mmname=%s'>点击</a>" %user.mmname.encode('utf-8')
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
		html = "<html><body><h3>无效的访问</h3></body></html>"
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
			html = "<html><body><h3>请登录!</h3></body></html>"
			return HttpResponse(html)
	else:
		html = "<html><body><h3>请登录!</h3></body></html>"
		return HttpResponse(html)


def unsolved(request):
	if request.method == "GET" and 'mmname' in request.GET:
		mmname = request.GET['mmname']
		userlist = User.objects.filter(mmname=mmname)
		qbname = userlist[0].qbname
		qbuserlist = QBUser.objects.filter(qbname=qbname)
		if len(qbuserlist) != 0:
			questionlist = Question.objects.filter(ques_owner=qbname, question_state="待解决")
			return render_to_response('questiontobesolvelist.html', {'qbname':qbname,'questions':questionlist})
		else:
			html = "<html><body><h3>请登录!</h3></body></html>"
			return HttpResponse(html)
	else:
		html = "<html><body><h3>请登录!</h3></body></html>"
		return HttpResponse(html)


def register(request):
	if request.method == "GET" and 'mmname' in request.GET:
		mmname = request.GET['mmname']
		return render_to_response('register.html', {'mmname':mmname, 'state':'unknown'})
	elif request.method == "POST" and 'mmname' in request.POST:
		mmname = request.POST['mmname']
		qbname = request.POST['name']
		password = request.POST['password']
		confirm = request.POST['confirm']
		if qbname == '' or password == '':
			return render_to_response('register.html', {'mmname':mmname, 'state':'null'})
		if password != confirm:
			return render_to_response('register.html', {'mmname':mmname, 'state':'different'})
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
			return render_to_response('register.html', {'mmname':mmname, 'state':'success'})
		else:
			return render_to_response('register.html', {'mmname':mmname, 'state':'existed'})
	else:
		if request.method == "POST":
			for key in request.POST:
				print key
		html = "<html><body><h3>无效的访问</h3></body></html>"
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
		html = "<html><body><h3>%s</h3></body></html>" % helloword
		return HttpResponse(html)
	else:
		html = "<html><body>None</body></html>"
		return HttpResponse(html)
	
def index(request):
	helloword = "welcome to QuestionBird!"
	html = "<html><body><h3>%s</h3></body></html>" % helloword
	return HttpResponse(html)