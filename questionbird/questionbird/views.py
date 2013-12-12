#! /usr/bin/env python
# coding=utf-8
__author__ = 'ypxtq'

import hashlib, urllib2, urllib
import xml.etree.ElementTree as ET
import time, json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import smart_str, smart_unicode
from questionbird.keys import *
from questionbird.models import *
from django.shortcuts import *
from django.template import *


new_pass = ''
# Create your views here.
@csrf_exempt
#获取access_token的方法
def getAccessToken():
    access_json = urllib.urlopen(ACCESS_URL % (APP_ID, APP_SECRET))
    resp = json.loads(access_json.read())
    return resp['access_token']


def handleRequest(request):
	if request.method == 'GET':
		#response = HttpResponse(request.GET['echostr'])
		response = HttpResponse(checkSignature(request), content_type="text/plain")
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


def create_user(mmname):
	user = User(mmname=mmname, qbname='', password='', last_oper=0)
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
	#处理语音消息
	elif message_type == "voice":
		response_msg = handle_voice(msg, user[0])
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
				ques_owner=user.qbname, content='', category='',
				question_state='已选科', answer='', answer_state='',
				answer_satis='', answer_eva='', solver_name='')
			if content in CATEGORY_DIC:
				question.category = CATEGORY_DIC[content]
				question.save()
				user.last_oper = 101
				response = '您的问题类型为:%s\n\r请输入您要提问的内容:' % question.category
			else:
				response = '无效的选项，请重新输入'
				user.last_oper = 100
	elif user.last_oper == 101:
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			questionlist = Question.objects.filter(ques_owner=user.qbname, question_state='已选科')
			if len(questionlist) == 0:
				response = "未知的错误!请重新点击'我要提问'按钮开始提问"
				user.last_oper = 0
			else:
				question = questionlist[0]
				question.content = content
				question.question_state = '待解决'
				user.last_oper = 0
				question.save()
				qbuser = QBUser.objects.get(qbname=user.qbname)
				qbuser.learncoin -= 2
				qbuser.question_num += 1
				qbuser.unsolved_num += 1
				qbuser.save()
				response = '提问成功，半小时内将有老师为您解答，请耐心等待~'
	elif user.last_oper == 102:
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			qbuserlist = QBUser.objects.filter(qbname=user.qbname)
			questionlist = Question.objects.filter(ques_owner=user.qbname)
			if len(qbuserlist) == 0:
				response = "未知的错误!请重新点击'更改昵称'按钮修改您的昵称"
				user.last_oper = 0
			else:
				qbuser = qbuserlist[0]
				qbuser.qbname = content
				qbuser.save()
				user.qbname = content
				user.save()
				for i in range(0, len(questionlist)):
					questionlist[i].ques_owner = content
					questionlist[i].save()
				response = '修改成功!您好，%s' % (qbuser.qbname)
				user.last_oper = 0
	elif user.last_oper == 103:
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			if user.password == content:
				response = "请输入新密码:"
				user.last_oper = 104
			else:
				response = "输入错误，请重新输入:"
				user.last_oper = 103
	elif user.last_oper == 104:
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			global new_pass
			new_pass = content
			response = "请再次输入:"
			user.last_oper = 105
	elif user.last_oper == 105:
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			global new_pass
			qbuserlist = QBUser.objects.filter(qbname=user.qbname)
			if len(qbuserlist) == 0:
				response = "未知的错误!请重新点击'更改密码'按钮修改您的密码"
				user.last_oper = 0
			elif new_pass == content:
				qbuser = qbuserlist[0]
				qbuser.password = content
				qbuser.save()
				user.password = content
				user.save()
				response = "修改成功!"
				user.last_oper = 0
			else:
				response = "两次输入不同，请重新输入新密码:"
				user.last_oper = 104
	elif user.last_oper == 106:
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			qbuserlist = QBUser.objects.filter(qbname=user.qbname)
			if len(qbuserlist) == 0:
				response = "未知的错误!请重新点击'更改年级'按钮修改您的年级"
				user.last_oper = 0
			else:
				if content in CATEGORY_GRADE_DIC:
					qbuser = qbuserlist[0]
					qbuser.grade = CATEGORY_GRADE_DIC[content]
					qbuser.save()
					response = '修改成功!'
					user.last_oper = 0
				else:
					response = '无效的选项，请重新输入'
					user.last_oper = 106
	elif user.last_oper == 107:
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			suggestion = Suggestion(content=content)
			suggestion.save()
			response = "谢谢您的建议，闻题鸟将在您的帮助下更加完善。"
			user.last_oper = 0
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
		login = "<a href='http://questionbird.sinaapp.com/login/?mmname=%s'>登录</a>" % user.mmname.encode('utf-8')
		register = "<a href='http://questionbird.sinaapp.com/register/?mmname=%s'>注册</a>" % user.mmname.encode('utf-8')
		response = "请选择需要的操作:\n\r%s     %s" % (login, register)
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
			response = "已解决问题的列表页面已为您准备好，请<a href='http://questionbird.sinaapp.com/solved/?mmname=%s'>点击</a>" % user.mmname.encode(
				'utf-8')
			user.last_oper = 0
	elif eventKey == E_KEY_UNSOLVED:
		if len(user.qbname) == 0:
			response = '请先登录!'
			user.last_oper = 0
		else:
			response = "待解决问题的列表页面已为您准备好，请<a href='http://questionbird.sinaapp.com/unsolved/?mmname=%s'>点击</a>" % user.mmname.encode(
				'utf-8')
			user.last_oper = 0
	elif eventKey == E_KEY_INFO:
		if len(user.qbname) == 0:
			response = '请先登录!'
			user.last_oper = 0
		else:
			qbuser = QBUser.objects.get(qbname=user.qbname)
			response = "您的个人信息:\n\r昵称:%s\n\r年级:%s\n\r剩余学习币:%d\n\r已提问次数:%d\n\r待解决问题数:%d" % (
				qbuser.qbname.encode('utf-8'), qbuser.grade.encode('utf-8'), qbuser.learncoin, qbuser.question_num,
				qbuser.unsolved_num)
			user.last_oper = 0
	elif eventKey == E_KEY_NICKNAME:
		if len(user.qbname) == 0:
			response = '请先登录!'
			user.last_oper = 0
		else:
			response = '请输入您的新昵称:'
			user.last_oper = 102
	elif eventKey == E_KEY_PASS:
		if len(user.qbname) == 0:
			response = '请先登录!'
			user.last_oper = 0
		else:
			response = '请输入原密码:'
			user.last_oper = 103
	elif eventKey == E_KEY_GRADE:
		#尚未登录
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			response = "请选择新的年级:\n\r1.小学一年级\n\r2.小学二年级\n\r3.小学三年级\n\r4.小学四年级\n\r5.小学五年级\n\r6.小学六年级\n\r7.初中一年级\n\r8.初中二年级\n\r9.初中三年级\n\r10.高中一年级\n\r11.高中二年级\n\r12.高中三年级"
			user.last_oper = 106
	elif eventKey == E_KEY_PRODUCT:
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			response = "闻题鸟微信服务号V1.0由一盆小铜钱小组为您敬上。了解更多我们的信息请致电15959542364。"
			user.last_oper = 0
	elif eventKey == E_KEY_FEEDBACK:
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			response = "尊敬的用户您好，欢迎发送任何您的意见和建议:"
			user.last_oper = 107
	elif eventKey == E_KEY_ACTIVITY:
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			response = "暂时没有活动信息哦，敬请期待我们接下来推出的活动。"
			user.last_oper = 0
	else:
		#response = "Wrong Message Key!"
		exit(0)
	user.save()
	return response


def handle_voice(msg, user):
	response = ""
	response = "您刚刚说的是不是："
	if 'Recognition' in msg:
		response += msg.get("Recognition")
	user.save()
	return response


# 打包消息xml，作为返回    
def pack_text_xml(post_msg, response_msg):
	text_tpl = '''<xml>
				<ToUserName><![CDATA[%s]]></ToUserName>
				<FromUserName><![CDATA[%s]]></FromUserName>
				<CreateTime>%s</CreateTime>
				<MsgType><![CDATA[%s]]></MsgType>
				<Content><![CDATA[%s]]></Content>
				<FuncFlag>0</FuncFlag>
				</xml>'''
	text_tpl = text_tpl % (
		post_msg['FromUserName'], post_msg['ToUserName'], str(int(time.time())), 'text', response_msg)
	# 调换发送者和接收者，然后填入需要返回的信息到xml中
	return text_tpl


def test(request):
	user = User.objects.filter(qbname='yo')
	if len(user) == 0:
		html = "<html><body><a href='www.baidu.com/?name=%s'>123</a></body></html>" % 'hahaha'
	else:
		html = "<html><body><a href='www.baidu.com/?name=%s'>123</a></body></html>" % user[0].password
	return HttpResponse(html)


def solved(request):
	if request.method == "GET" and 'mmname' in request.GET:
		mmname = request.GET['mmname']
		userlist = User.objects.filter(mmname=mmname)
		qbname = userlist[0].qbname
		qbuserlist = QBUser.objects.filter(qbname=qbname)
		if len(qbuserlist) != 0:
			questionlist = Question.objects.filter(ques_owner=qbname, question_state="已解决")
			return render_to_response('questionsolvedlist.html', {'qbname': qbname, 'questions': questionlist})
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
			return render_to_response('questiontobesolvelist.html', {'qbname': qbname, 'questions': questionlist})
		else:
			html = "<html><body><h3>请登录!</h3></body></html>"
			return HttpResponse(html)
	else:
		html = "<html><body><h3>请登录!</h3></body></html>"
		return HttpResponse(html)


def register(request):
	if request.method == "GET" and 'mmname' in request.GET:
		mmname = request.GET['mmname']
		return render_to_response('register.html', {'mmname': mmname, 'state': 'unknown'})
	elif request.method == "POST" and 'mmname' in request.POST:
		mmname = request.POST['mmname']
		qbname = request.POST['name']
		password = request.POST['password']
		confirm = request.POST['confirm']
		if qbname == '' or password == '':
			return render_to_response('register.html', {'mmname': mmname, 'state': 'null'})
		if password != confirm:
			return render_to_response('register.html', {'mmname': mmname, 'state': 'different'})
		qbuserlist = QBUser.objects.filter(qbname=qbname)
		if len(qbuserlist) == 0:
			qbuser = QBUser(qbname=qbname, password=password, learncoin=200, question_num=0, unsolved_num=0,
							grade="小学一年级")
			qbuser.save()
			userlist = User.objects.filter(mmname=mmname)
			user = userlist[0]
			user.qbname = request.POST['name']
			user.password = request.POST['password']
			user.last_oper = 0
			user.save()
			return render_to_response('register.html', {'mmname': mmname, 'state': 'success'})
		else:
			return render_to_response('register.html', {'mmname': mmname, 'state': 'existed'})
	else:
		html = "<html><body><h3>无效的访问</h3></body></html>"
		return HttpResponse(html)


def login(request):
	if request.method == "GET" and 'mmname' in request.GET:
		mmname_value = request.GET['mmname']
		return render_to_response('login.html', {'mmname': mmname_value})
	elif request.method == "POST" and 'mmname' in request.POST:
		mmname = request.POST['mmname']
		qbname = request.POST['name']
		password = request.POST['password']
		if qbname == '' or password == '':
			return render_to_response('login.html', {'mmname': mmname, 'state': 'null'})
		qbuserlist = QBUser.objects.filter(qbname=qbname)
		if len(qbuserlist) != 0:
			qbuser = qbuserlist[0]
			if qbuser.qbname == qbname and qbuser.password == password:
				userlist = User.objects.filter(mmname=mmname)
				user = userlist[0]
				user.qbname = qbname
				user.password = password
				user.last_oper = 0
				user.save()
				return render_to_response('login.html', {'mmname': mmname, 'state': 'success'})
			else:
				return render_to_response('login.html', {'mmname': mmname, 'state': 'fail'})
		else:
			return render_to_response('login.html', {'mmname': mmname, 'state': 'unexisted'})
	else:
		html = "<html><body><h3>无效的访问</h3></body></html>"
		return HttpResponse(html)


def index(request):
	helloword = "welcome to QuestionBird!"
	html = "<html><body><h3>%s</h3></body></html>" % helloword
	return HttpResponse(html)


def login_teacher(request):
	if request.method == "GET":
		return render_to_response('login_teacher.html', {'state': 'unknown'})
	else:
		teachername = request.POST['name']
		password = request.POST['password']
		teacherlist = Teacher.objects.filter(teachername=teachername)
		if teachername == '' or password == '':
			return render_to_response('login_teacher.html', {'state': 'null'})
		elif len(teacherlist) == 0:
			return render_to_response('login_teacher.html', {'state': 'nonexisted'})
		elif teacherlist[0].password != password:
			return render_to_response('login_teacher.html', {'state': 'wrong'})
		else:
			return render_to_response('login_teacher.html', {'state': 'unknown'})