#! /usr/bin/env python
# coding=utf-8

__author__ = 'ypxtq'

import hashlib, urllib2, urllib, httplib
import xml.etree.ElementTree as ET
import time, json
import os
from django.http import HttpResponse,HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import smart_str, smart_unicode
from questionbird.keys import *
from questionbird.models import *
from django.shortcuts import *
from django.template import *
from django.utils import simplejson

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

new_pass = ''
# Create your views here.
@csrf_exempt
#获取access_token的方法
def get_accessToken():
	access_json = urllib.urlopen(ACCESS_URL % (APP_ID, APP_SECRET))
	resp = json.loads(access_json.read())
	return resp['access_token']

#主动向用户发送文字消息
def post_message_text(touser, text):
	message = {
			"touser":touser,
			"msgtype":"text",
			"text":{"content":text}
	}
	access_token = get_accessToken()
	url = POST_URL%access_token
	request = urllib2.Request(url, json.dumps(message, ensure_ascii=False))
	response = urllib2.urlopen(request)

#主动向用户发送图文消息
def post_message_pic(touser, picurl, text):
	message = {
			"touser":touser,
			"msgtype":"news",
			"news":{"articles":[{"title":"问题解答", "description":text, "picurl":"http://image.baidu.com/channel#%E6%91%84%E5%BD%B1&%E5%A9%9A%E7%BA%B1%E6%91%84%E5%BD%B1&0&0"}]}
	}
	access_token = get_accessToken()
	url = POST_URL%access_token
	request = urllib2.Request(url, json.dumps(message, ensure_ascii=False))
	response = urllib2.urlopen(request)

#主动向用户发送语音消息
def post_message_voice(touser, voiceurl):
	message = {
			"touser":touser,
			"msgtype":"music",
			"music":{
					"title":"教师录音",
					"description":"问题解答的补充录音",
					"musicurl":"http://zhangmenshiting.baidu.com/data2/music/7298575/717071775600128.mp3?xcode=87517c89e8ed706585891ec932ec1c2cac0aeb26238b4679",
					"hqmusicurl":"http://zhangmenshiting.baidu.com/data2/music/7298575/717071775600128.mp3?xcode=87517c89e8ed706585891ec932ec1c2cac0aeb26238b4679",
					"thumb_media_id":"HEADvWi-_0hX7J8GzvJgJJoOSADzAumMtsbnVNFuIhgMwL0Jz3I-tps4bztfya9X"
			}
	}
	access_token = get_accessToken()
	url = POST_URL%access_token
	request = urllib2.Request(url, json.dumps(message, ensure_ascii=False))
	response = urllib2.urlopen(request)

def download_file(media_id, name):
	access_token = get_accessToken()
	url = DOWNLOAD_URL%(access_token, media_id)
	f = urllib.urlopen(url)
	data = f.read()
	dst = open(name, 'wb+')
	dst.write(data)
	f.close()
	dst.close()


# #上传文件到微信服务器
# def upload_file(name, filetype):
# 	access_token = get_accessToken()
# 	url = UPLOAD_URL%(access_token, filetype)
# 	src = open(name, 'wb+')
# 	data = src.read()
# 	f.close()
# 	request = urllib2.Request(url, json.dumps(message, ensure_ascii=False))
# 	response = urllib2.urlopen(request)


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


#check whether the token is valid
def checkSignature(request):
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
	rawStr = request.read()
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
	elif message_type == "image":
		response_msg = handle_picture(msg, user[0])
	else:
		response_msg = '我看不懂你在说些什么。'
	# 返回消息
	return pack_text_xml(msg, response_msg)


def handle_text(msg, user):
	content = msg.get("Content")
	response = ""
	#选科目
	if user.last_oper == 100:
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			questionlist = Question.objects.filter(ques_owner=user.qbname, question_state='已选科')
			if len(questionlist) == 0:
				question = Question(
					ques_owner=user.qbname, content='', category='',
					ques_image='', ques_voice='', 
					question_state='已选科', answer='', answer_state='',
					answer_satis='', answer_eva='', solver_name='')
			else:
				question = questionlist[0]
			#检测是否有因用户误操作而未完成的问题，并删除
			unfinishedquestionlist = Question.objects.filter(ques_owner=user.qbname, question_state='待加图')
			if len(unfinishedquestionlist) != 0:
				for unfinished in unfinishedquestionlist:
					unfinished.delete()
			if content in CATEGORY_DIC:
				question.category = CATEGORY_DIC[content]
				question.save()
				user.last_oper = 110
				response = '您的问题科目为:%s\n\r请输入您的问题(语音或文字):' % question.category
			else:
				response = '无效的选项，请输入正确的科目序号！\n\r请重新输入:'
				user.last_oper = 100
	#提问
	elif user.last_oper == 110:
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
				question.question_state = '待加图'
				user.last_oper = 120
				response = "您的问题是：%s\n\r您还可以选择上传一张图片，也可直接回复任意文字消息结束本次提问。" %content
				question.save()
	#加图
	elif user.last_oper == 120:
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			questionlist = Question.objects.filter(ques_owner=user.qbname, question_state='待加图')
			if len(questionlist) == 0:
				response = "未知的错误!请重新点击'我要提问'按钮开始提问"
				user.last_oper = 0
			else:
				question = questionlist[0]
				question.question_state = '待解决'
				question.save()
				qbuser = QBUser.objects.get(qbname=user.qbname)
				qbuser.learncoin -= 2
				qbuser.question_num += 1
				qbuser.unsolved_num += 1
				qbuser.save()
				response = "提问成功，半小时内将有老师为您解答，请耐心等待~"
				user.last_oper = 0
	#更改昵称
	elif user.last_oper == 200:
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
	#更改密码
	elif user.last_oper == 300:
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			qbuserlist = QBUser.objects.filter(qbname=user.qbname)
			qbuser = qbuserlist[0]
			qbuser.password = content
			qbuser.save()
			user.password = content
			user.save()
			response = "修改成功!"
			user.last_oper = 0
	#更改年级
	elif user.last_oper == 400:
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
					user.last_oper = 400
	#建议
	elif user.last_oper == 500:
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			suggestion = Suggestion(content=content)
			suggestion.save()
			response = "谢谢您的建议，闻题鸟将在您的帮助下更加完善。"
			user.last_oper = 0
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
		login = "<a href='%slogin/?mmname=%s'>登录</a>" % (SERVER_URL, user.mmname)
		register = "<a href='%sregister/?mmname=%s'>注册</a>" % (SERVER_URL, user.mmname)
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
			response = "请选择问题所属科目:\n\r1.小学语文\n\r2.小学数学\n\r3.初中语文\n\r4.初中数学\n\r5.初中英语\n\r6.高中语文\n\r7.高中数学\n\r8.高中英语"
			user.last_oper = 100
	elif eventKey == E_KEY_SOLVED:
		if len(user.qbname) == 0:
			response = '请先登录!'
			user.last_oper = 0
		else:
			response = "已解决问题的列表页面已为您准备好，请<a href='%ssolved/?mmname=%s'>点击</a>" % (SERVER_URL, user.mmname)
			user.last_oper = 0
	elif eventKey == E_KEY_UNSOLVED:
		if len(user.qbname) == 0:
			response = '请先登录!'
			user.last_oper = 0
		else:
			response = "待解决问题的列表页面已为您准备好，请<a href='%sunsolved/?mmname=%s'>点击</a>" % (SERVER_URL, user.mmname)
			user.last_oper = 0
	elif eventKey == E_KEY_INFO:
		if len(user.qbname) == 0:
			response = '请先登录!'
			user.last_oper = 0
		else:
			qbuser = QBUser.objects.get(qbname=user.qbname)
			response = "您的个人信息:\n\r昵称:%s\n\r年级:%s\n\r剩余学习币:%d\n\r已提问次数:%d\n\r待解决问题数:%d" % (
				qbuser.qbname, qbuser.grade, qbuser.learncoin, qbuser.question_num,
				qbuser.unsolved_num)
			user.last_oper = 0
	elif eventKey == E_KEY_NICKNAME:
		if len(user.qbname) == 0:
			response = '请先登录!'
			user.last_oper = 0
		else:
			response = '请输入您的新昵称:'
			user.last_oper = 200
	elif eventKey == E_KEY_PASS:
		if len(user.qbname) == 0:
			response = '请先登录!'
			user.last_oper = 0
		else:
			response = '请输入新密码:'
			user.last_oper = 300
	elif eventKey == E_KEY_GRADE:
		#尚未登录
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			response = "请选择新的年级:\n\r1.小学一年级\n\r2.小学二年级\n\r3.小学三年级\n\r4.小学四年级\n\r5.小学五年级\n\r6.小学六年级\n\r7.初中一年级\n\r8.初中二年级\n\r9.初中三年级\n\r10.高中一年级\n\r11.高中二年级\n\r12.高中三年级"
			user.last_oper = 400
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
			user.last_oper = 500
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
	if user.last_oper == 110:
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			questionlist = Question.objects.filter(ques_owner=user.qbname, question_state='已选科')
			if len(questionlist) == 0:
				response = "未知的错误!请重新点击'我要提问'按钮开始提问"
				user.last_oper = 0
			else:
				media_id=msg.get("MediaId")
				path = STORE_PATH + media_id + '.' + msg.get("Format")
				download_file(media_id, path)
				question = questionlist[0]
				question.question_state = '待加图'
				question.ques_voice = "\\site_media\\files\\"+media_id+'.'+msg.get("Format")
				question.content = msg.get("Recognition")
				question.save()
				response = "您要提的问题是：%s\n\r您还可以选择上传一张图片，也可直接回复任意文字消息结束本次提问。"%msg.get("Recognition")
				user.last_oper = 120
	else:
		response = "您刚刚说的是不是："
		if 'Recognition' in msg:
			response += msg.get("Recognition")
		user.last_oper = 0;
	user.save()
	return response


def handle_picture(msg, user):
	response = ""
	if user.last_oper == 120:
		if user.qbname == '':
			response = "请先登录!"
			user.last_oper = 0
		else:
			questionlist = Question.objects.filter(ques_owner=user.qbname, question_state='待加图')
			if len(questionlist) == 0:
				response = "未知的错误!请重新点击'我要提问'按钮开始提问"
				user.last_oper = 0
			else:
				media_id=msg.get("MediaId")
				path = STORE_PATH + media_id + '.jpg'
				download_file(media_id, path)
				question = questionlist[0]
				question.question_state = '待解决'
				question.ques_image = "\\site_media\\files\\"+media_id+'.jpg'
				question.save()
				qbuser = QBUser.objects.get(qbname=user.qbname)
				qbuser.learncoin -= 2
				qbuser.question_num += 1
				qbuser.unsolved_num += 1
				qbuser.save()
				response = "提问成功，半小时内将有老师为您解答，请耐心等待~"
				user.last_oper = 0
	else:
		response = "pic url:%s\n, pic mid:%s\n" %(msg.get("PicUrl"), msg.get("MediaId"))
		user.last_oper = 0;
	user.save()
	return response


# 打包消息xml，作为返回    
def pack_text_xml(msg, response_msg):
	text_tpl = '''<xml>
				<ToUserName><![CDATA[%s]]></ToUserName>
				<FromUserName><![CDATA[%s]]></FromUserName>
				<CreateTime>%s</CreateTime>
				<MsgType><![CDATA[%s]]></MsgType>
				<Content><![CDATA[%s]]></Content>
				<FuncFlag>0</FuncFlag>
				</xml>'''
	text_tpl = text_tpl % (
		msg['FromUserName'], msg['ToUserName'], str(int(time.time())), 'text', response_msg)
	# 调换发送者和接收者，然后填入需要返回的信息到xml中
	return text_tpl


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

def test(request):
	# access_token = get_accessToken()
	# media_id = 'ym_bAlEXOlEXA51PzcTVArSjUV-TV9nbMRI9N6w_ZDwUYHaDncWYcqi53kxevzG6'
	# # url = 'http://file.api.weixin.qq.com/cgi-bin/media/get?access_token=%s&media_id=%s'%(access_token,media_id)
	# name = STORE_PATH+'1.jpg'
	# download_file(media_id, name)
	html = "<html><body><a href='http://www.baidu.com'>123</a></body></html>"
	touser = 'oUJnEt9HWfBYQjtPDdOnIpWB2zSk'
	# touser1 = 'oUJnEt3IE3K9Chy7mEs9fO5zu1_Q'
	text = "Helloworld"
	user = User.objects.filter(qbname="123")
	if user[0].mmname != touser:
		html = "<html><body><a href='http://www.baidu.com'>%s</a></body></html>"%user[0].mmname
		post_message_text(user[0].mmname,"您的问题已解决。")
	else:
		html = "<html><body><a href='http://www.baidu.com'>1234s</a></body></html>"
		post_message_text(user[0].mmname.encode('utf-8'),"您的问题已解决个屁。")
	# post_message_text(touser,text)
	# post_message_voice(touser, 123)
	return HttpResponse(html)

def login_teacher(request):
	if request.method == "GET":
		return render_to_response('login_teacher.html', {'state': 'unknown'})
	elif request.method == "POST" and 'name' in request.POST:
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
			url = '/questions_teacher/'
			request.session['teacherid'] = teacherlist[0].id
			return HttpResponseRedirect(url)
	else:
		html = "<html><body>None</body></html>"
		return HttpResponse(html)
@csrf_exempt
def register_teacher(request):
	if request.method == "GET":
		return render_to_response('register_teacher.html')
	elif request.method == "POST":
		name = request.POST['name']
		password = request.POST['password']
		inviteNumber = request.POST['inviteNumber']
		number = RequestCode.objects.filter(request_code=inviteNumber)
		if len(number) == 0:
			return HttpResponse(simplejson.dumps({'state':'invite'}),mimetype='application/json')
		subjects = request.POST.getlist('subjects')
		sublen = len(subjects)
		str = "";
		for i in subjects:
			str += i
		qbuserlist = Teacher.objects.filter(teachername=name)
		if len(qbuserlist) == 0:
			qbuser = Teacher(teachername=name, password=password, subjects=str)
			qbuser.save()
			return HttpResponse(simplejson.dumps({"state":'success'}),mimetype='application/json')
		else:
			return HttpResponse(simplejson.dumps({'state': 'existed'}),mimetype='application/json')
	else:
		return render_to_response('register_teacher.html')

def questions_teacher(request):
	if request.method == "GET":
		if request.session.has_key('teacherid'):
			teacherid = request.session['teacherid']
			teacherlist = Teacher.objects.filter(id=teacherid)
			chinese = teacherlist[0].subjects.find('chinese')
			english = teacherlist[0].subjects.find('english')
			math = teacherlist[0].subjects.find('math')
			unChineseQuestion = Question.objects.filter(category__contains="语文",question_state='待解决')
			unMathQuestion = Question.objects.filter(category__contains="数学",question_state='待解决')
			unEnglishQuestion = Question.objects.filter(category__contains="英语",question_state='待解决')
			chineseQuestion = Question.objects.filter(category__contains="语文",question_state='已解决',solver_name=teacherlist[0].teachername)
			mathQuestion = Question.objects.filter(category__contains="数学",question_state='已解决',solver_name=teacherlist[0].teachername)
			englishQuestion = Question.objects.filter(category__contains="英语",question_state='已解决',solver_name=teacherlist[0].teachername)
			resultSolved = []
			resultUnsolved = []
			if chinese !=-1:
				resultUnsolved += unChineseQuestion
				resultSolved += chineseQuestion
			if english != -1:
				resultUnsolved += unEnglishQuestion
				resultSolved += englishQuestion
			if math != -1:
				resultUnsolved += unMathQuestion
				resultSolved += mathQuestion
			return render_to_response('questions_teacher.html', {'teachername': teacherlist[0].teachername, 'unsolve': resultUnsolved, 'solve': resultSolved})
	else:
		html = "<html><body>None</body></html>"
		return HttpResponse(html)

@csrf_exempt
def answer(request):
	if request.method == 'POST':
		questionid = request.POST["id"]
		question = Question.objects.get(id=questionid)
		if not request.POST.has_key('voice'):
			filename = time.strftime("%Y%m%d%H%M%S")
			file = request.FILES['voice']
			filename = filename+file.name[file.name.find('.'):]
			question.answer_voice = '\\site_media'+'\\files\\'+filename
			filename = STORE_PATH+filename
			destinaton = open(filename,'wb')
			for chunk in file.chunks():
				destinaton.write(chunk)
			destinaton.close()
		elif  not request.POST.has_key('image'):
			filename = time.strftime("%Y%m%d%H%M%S")
			file = request.FILES['image']
			filename = filename+file.name[file.name.find('.'):]
			question.answer_image = '\\site_media'+'\\files\\'+filename
			filename = STORE_PATH+filename
			destinaton = open(filename,'wb')
			for chunk in file.chunks():
				destinaton.write(chunk)
			destinaton.close()
		if  request.POST['answerword']:
			question.answer = request.POST['answerword']
		question.solver_name = request.POST['solver']
		question.question_state = "已解决"
		question.save()
		user = User.objects.filter(qbname=question.ques_owner)
		text = "您的解答是："+question.answer
		post_message_text(user[0].mmname.encode('utf-8'),text.encode('utf-8'))
		return HttpResponse(simplejson.dumps({"state":'success',"content":question.content,'ques_image':question.ques_image,'ques_voice':question.ques_voice,'category':question.category,'question_state':question.question_state,'answer':question.answer,'answer_image':question.answer_image,'answer_voice':question.answer_voice,'answer_state':question.answer_state,'answer_satis':question.answer_satis,'answer_eva':question.answer_eva,'solver_name':question.solver_name}),mimetype='application/json')