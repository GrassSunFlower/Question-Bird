#! /usr/bin/env python
# coding=utf-8

__author__ = 'ypxtq'

import hashlib, urllib2, urllib, httplib,smtplib 
import xml.etree.ElementTree as ET
import time, json
import os,random
from django.http import HttpResponse,HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import smart_str, smart_unicode
from questionbird.keys import *
from questionbird.models import *
from django.shortcuts import *
from django.template import *
from django.utils import simplejson
from email.mime.text import MIMEText  
import string
import os

import sys

reload(sys)
sys.setdefaultencoding('utf-8')

return_type = 'text'
# Create your views here.
@csrf_exempt
#获取access_token的方法
def get_accessToken():
    access_json = urllib.urlopen(ACCESS_URL % (APP_ID, APP_SECRET))
    resp = json.loads(access_json.read())
    return resp['access_token']

def get_user_name(openid):
    access_token = get_accessToken()
    url = GET_NAME_URL%(access_token, openid)
    access_json = urllib.urlopen(url)
    resp = json.loads(access_json.read())
    return resp['nickname']

#主动向用户发送文字消息
def post_message_text(touser, content):
    message = {
            "touser":touser,
            "msgtype":"text",
            "text":{"content":content}
            }
    access_token = get_accessToken()
    url = POST_URL%access_token
    request = urllib2.Request(url, json.dumps(message, ensure_ascii=False))
    response = urllib2.urlopen(request)


def post_message_no_pic(touser, content, answer, ques_id):
    url = "%s/single_question/?id=%d" % (SERVER_URL, ques_id)
    message = {
            "touser":touser,
            "msgtype":"news",
            "news":{
                "articles":
                    [{
                        "title":"问题解答",
                        "picurl":SERVER_URL+'/site_media/img/header.jpg',
                        'url':url
                    },
                    {
                        "title":"问题内容:\n\r"+content,
                        'url':url
                    },
                    {
                        "title":"解答内容:\n\r"+answer,
                        'url':url
                    },
                    {
                        "title":"查看详细解答请点击",
                        'url':url
                    }]
                }
    }
    access_token = get_accessToken()
    url = POST_URL%access_token
    request = urllib2.Request(url, json.dumps(message, ensure_ascii=False))
    response = urllib2.urlopen(request)


#主动向用户发送图文消息
def post_message_pic(touser, picurl, content, answer, ques_id):
    url = "%s/single_question/?id=%d" % (SERVER_URL, ques_id)
    message = {
            "touser":touser,
            "msgtype":"news",
            "news":{
                "articles":
                    [{
                        "title":"问题解答",
                        "picurl":SERVER_URL+'/site_media/img/header.jpg',
                        'url':url
                    },
                    {
                        "title":"问题内容:\n\r"+content,
                        'url':url
                    },
                    {
                        "title":"解答内容:\n\r"+answer,
                        "picurl":picurl,
                        'url':url
                    },
                    {
                        "title":"查看详细解答请点击",
                        'url':url
                    }]
                }
    }
    access_token = get_accessToken()
    url = POST_URL%access_token
    request = urllib2.Request(url, json.dumps(message, ensure_ascii=False))
    response = urllib2.urlopen(request)

#主动向用户发送语音消息
def post_message_voice(touser, voiceurl):
    content = "听老师的解答语音，请点<a href='%s'>这里</a>"%voiceurl
    message = {
            "touser":touser,
            "msgtype":"text",
            "text":{"content":content}
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
    user = QBUser(mmname=mmname, last_oper=0, learncoin=200, question_num=0, unsolved_num=0, grade='小学一年级', ques_id=-1)
    user.save()


def response_msg(request):
    # 从request中获取输入文本
    rawStr = request.read()
    # 将文本进行解析,得到请求的数据
    msg = parse_msg(ET.fromstring(rawStr))
    mmname = msg["FromUserName"]
    user = QBUser.objects.filter(mmname=mmname)
    if len(user) == 0:
        create_user(mmname)
    user = QBUser.objects.filter(mmname=mmname)
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
    global return_type
    if return_type == 'news':
        return_type = 'text'
        return response_msg
    else:
        return pack_text_xml(msg, response_msg)



def handle_text(msg, user):
    content = msg.get("Content")
    response = ""
    #选科目
    if user.last_oper == 100:
        questionlist = Question.objects.filter(ques_owner=user.mmname, question_state='已选科')
        if len(questionlist) == 0:
            question = Question(
                ques_owner=user.mmname, content='', category='',
                ques_image='', ques_voice='', question_state='已选科',
                answer='', answer_image='', answer_voice='',
                answer_state='', answer_satis=-1, answer_eva='', solver_name='',
                question_changing=-1, start_time='0', answer_time='0')
        else:
            question = questionlist[0]
        #检测是否有因用户误操作而未完成的问题，并删除
        unfinishedquestionlist = Question.objects.filter(ques_owner=user.mmname, question_state='待加图')
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
        questionlist = Question.objects.filter(ques_owner=user.mmname, question_state='已选科')
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
        questionlist = Question.objects.filter(ques_owner=user.mmname, question_state='待加图')
        if len(questionlist) == 0:
            response = "未知的错误!请重新点击'我要提问'按钮开始提问"
            user.last_oper = 0
        else:
            question = questionlist[0]
            question.question_state = '待解决'
            question.save()
            user.learncoin -= 2
            user.question_num += 1
            user.unsolved_num += 1
            user.last_oper = 0
            response = "提问成功，半小时内将有老师为您解答，请耐心等待~"
    elif user.last_oper == 200:
        name = get_user_name(user.mmname)
        question_bottle = QuestionBottle(ques_owner=user.mmname,owner_name=name,content=content,question_state='待解决',answer='',answer_name='')
        question_bottle.save()
        user.last_oper = 0
        response = "您的问题瓶已成功扔入大海，请静静等待有缘人吧~"
    elif user.last_oper == 300:
        question_bottle_list = QuestionBottle.objects.filter(id=user.ques_id)
        question_bottle = question_bottle_list[0]
        if question_bottle.question_state == '已解决':
            response = "已经有人在您之前将该问题解决了~再捡一个吧~"
            user.last_oper = 0
        else:
            question_bottle.answer = content
            answer_name = get_user_name(user.mmname)
            question_bottle.answer_name = answer_name
            question_bottle.question_state = "已解决"
            question_bottle.save()
            text = '您的问题瓶:%s\n\r已由用户:%s 解答，答案为：%s'%(question_bottle.content, question_bottle.answer_name, question_bottle.answer)
            post_message_text(question_bottle.ques_owner.encode('utf-8'), text.encode('utf-8'))
            user.last_oper = 0
            response = "用户%s已收到您的解答，谢谢您的热心解答~"%question_bottle.owner_name.encode('utf-8')
    #更改年级
    elif user.last_oper == 400:
        if content in CATEGORY_GRADE_DIC:
            user.grade = CATEGORY_GRADE_DIC[content]
            response = '修改成功!'
            user.last_oper = 0
        else:
            response = '无效的选项，请重新输入'
            user.last_oper = 400
    #建议
    elif user.last_oper == 500:
        suggestion = Suggestion(content=content)
        suggestion.save()
        response = "谢谢您的建议，闻题鸟将在您的帮助下更加完善。"
        user.last_oper = 0
    elif user.last_oper == 600:
        questionlist = Question.objects.filter(ques_owner=user.mmname, answer_state='待评分')
        if len(questionlist) == 0:
            user.last_oper = 0
            user.save()
        else:
            question = questionlist[0]
            if content == '1':
                question.answer_satis = 1
                teacherlist = Teacher.objects.filter(teachername=question.solver_name)
                teacher = teacherlist[0]
                teacher.wealth += 5
                teacher.save()
                question.answer_state = "待评价"
                question.save()
                user.last_oper = 610
                response = "评分提交成功，请继续输入评价："
            elif content == '0':
                question.answer_satis = 0
                question.answer_state = "待评价"
                question.save()
                user.last_oper = 610
                response = "评分提交成功，请继续输入不满意评价："
            else:
                user.last_oper = 600
                response = "无效的评分，请输入0-1中的某个分数。"
    elif user.last_oper == 610:
        questionlist = Question.objects.filter(ques_owner=user.mmname, answer_state='待评价')
        question = questionlist[0]
        question.answer_eva = content
        question.answer_state = "已评价"
        question.save()
        user.last_oper = 0
        response = "评价成功！"
    else:
        response = "请点击下面的按钮选择相应的服务~"
        user.last_oper = 0
    user.save()
    return response


def handle_event(msg, user):
    eventKey = msg.get("EventKey")
    if user.last_oper == 600:
        questionlist = Question.objects.filter(ques_owner=user.mmname, answer_state='待评分')
        if len(questionlist) == 0:
            user.last_oper = 0
            user.save()
        else:
            for question in questionlist:
                question.answer_state = "已评价"
                question.answer_eva = ""
                question.answer_satis = 1
                user.last_oper = 0
                teacherlist = Teacher.objects.filter(teachername=question.solver_name)
                teacher = teacherlist[0]
                teacher.wealth += 5
                teacher.save()
                question.save()
    elif user.last_oper == 610:
        questionlist = Question.objects.filter(ques_owner=user.mmname, answer_state='待评价')
        if len(questionlist) == 0:
            user.last_oper = 0
            user.save()
        else:
            for question in questionlist:
                question.answer_state = "已评价"
                question.answer_eva = ""
                user.last_oper = 0
                question.save()
    if msg.get("Event") == 'subscribe':
        response = "欢迎您来到闻题鸟的世界，这是一个自由的问题交流平台。在这里，难题不再有，问题不再留，清华北大优秀名师实时帮助您解答问题！如果有任何使用问题请点击右下角“关于我们”中的“使用帮助”"
    elif eventKey == E_KEY_ASK:
        if user.learncoin <= 2:
            response = "剩余学习币不足，请充值。"
            user.last_oper = 0
        else:
            response = "请选择问题所属科目:\n\r1.小学语文\n\r2.小学数学\n\r3.初中语文\n\r4.初中数学\n\r5.初中英语\n\r6.高中语文\n\r7.高中数学\n\r8.高中英语"
            user.last_oper = 100
    elif eventKey == E_KEY_THROW:
        response = "请输入您要扔的问题："
        user.last_oper = 200
    elif eventKey == E_KEY_PICK:
        question_bottle_list = QuestionBottle.objects.filter(question_state='待解决').exclude(ques_owner=user.mmname)
        if len(question_bottle_list) == 0:
            response = "很不幸，现在问题海中空荡荡的一个问题也没有~"
            user.last_oper = 0
            user.save()
            return response
        num = random.randint(0, len(question_bottle_list)-1)
        question_bottle = question_bottle_list[num]
        response = "您捡到了用户 %s 扔的一个问题瓶:\n\r%s\n\r欢迎您来进行回答:"%(question_bottle.owner_name, question_bottle.content)
        user.ques_id = question_bottle.id
        user.last_oper = 300
    elif eventKey == E_KEY_SOLVED:
        questionlist = Question.objects.filter(ques_owner=user.mmname, question_state='已解决')
        if len(questionlist) == 0:
            response = "您暂无任何已解决的问题。"
            user.last_oper = 0
            user.save()
            return response
        elif len(questionlist) >= 3:
            num = 3
        else:
            num = len(questionlist)
        global return_type
        return_type = 'news'
        more_url = "%s/solved/?mmname=%s" % (SERVER_URL, user.mmname)
        response = '''<xml>
                    <ToUserName><![CDATA[%s]]></ToUserName>
                    <FromUserName><![CDATA[%s]]></FromUserName>
                    <CreateTime>%s</CreateTime>
                    <MsgType><![CDATA[news]]></MsgType>
                    <ArticleCount>%s</ArticleCount>
                    <Articles>
                    '''% (msg['FromUserName'], msg['ToUserName'], str(int(time.time())), str(num+2))
        response += '''<item>
                    <Title><![CDATA[%s]]></Title>
                    <Url><![CDATA[%s]]></Url>
                    <PicUrl><![CDATA[%s]]></PicUrl>
                    </item>
                    '''% ("您的已解决问题列表", more_url, SERVER_URL+'/site_media/img/header_solved.jpg')
        for i in range(0, num):
            url = SERVER_URL+'/single_question/?id=%d'%questionlist[i].id
            if questionlist[i].ques_image != '':
                picurl = SERVER_URL + questionlist[i].ques_image
                response += '''<item>
                            <Title><![CDATA[%s]]></Title>
                            <PicUrl><![CDATA[%s]]></PicUrl>
                            <Url><![CDATA[%s]]></Url>
                            </item>
                            '''% (str(i+1)+'.'+questionlist[i].content, picurl, url)
            else:
                response += '''<item>
                            <Title><![CDATA[%s]]></Title>
                            <Url><![CDATA[%s]]></Url>
                            </item>
                            '''% (str(i+1)+'.'+questionlist[i].content, url)
        response += '''<item>
                        <Title><![CDATA[%s]]></Title>
                        <Url><![CDATA[%s]]></Url>
                        </item>
                        '''% ("查看全部", more_url)
        response += '''</Articles>
                    </xml>'''
        return response
        user.last_oper = 0
    elif eventKey == E_KEY_UNSOLVED:
        questionlist = Question.objects.filter(ques_owner=user.mmname, question_state='待解决')
        if len(questionlist) == 0:
            response = "您暂无任何待解决的问题。"
            user.last_oper = 0
            user.save()
            return response
        elif len(questionlist) >= 3:
            num = 3
        else:
            num = len(questionlist)
        global return_type
        return_type = 'news'
        more_url = "%s/unsolved/?mmname=%s" % (SERVER_URL, user.mmname)
        response = '''<xml>
                    <ToUserName><![CDATA[%s]]></ToUserName>
                    <FromUserName><![CDATA[%s]]></FromUserName>
                    <CreateTime>%s</CreateTime>
                    <MsgType><![CDATA[news]]></MsgType>
                    <ArticleCount>%s</ArticleCount>
                    <Articles>
                    '''% (msg['FromUserName'], msg['ToUserName'], str(int(time.time())), str(num+2))
        response += '''<item>
                    <Title><![CDATA[%s]]></Title>
                    <Url><![CDATA[%s]]></Url>
                    <PicUrl><![CDATA[%s]]></PicUrl>
                    </item>
                    '''% ("您的待解决问题列表", more_url, SERVER_URL+'/site_media/img/header_unsolved.jpg')
        for i in range(0, num):
            url = SERVER_URL+'/single_question/?id=%d'%questionlist[i].id
            if questionlist[i].ques_image != '':
                picurl = SERVER_URL + questionlist[i].ques_image
                response += '''<item>
                            <Title><![CDATA[%s]]></Title>
                            <PicUrl><![CDATA[%s]]></PicUrl>
                            <Url><![CDATA[%s]]></Url>
                            </item>
                            '''% (str(i+1)+'.'+questionlist[i].content, picurl, url)
            else:
                response += '''<item>
                            <Title><![CDATA[%s]]></Title>
                            <Url><![CDATA[%s]]></Url>
                            </item>
                            '''% (str(i+1)+'.'+questionlist[i].content, url)
        response += '''<item>
                        <Title><![CDATA[%s]]></Title>
                        <Url><![CDATA[%s]]></Url>
                        </item>
                        '''% ("查看全部", more_url)
        response += '''</Articles>
                    </xml>'''
        return response
    elif eventKey == E_KEY_INFO:
        text = "年级:%s\n\r剩余学习币:%d\n\r已提问次数:%d\n\r待解决问题数:%d" %(user.grade,user.learncoin,user.question_num,user.unsolved_num)
        url = '/user_info/?mmname=%s'%user.mmname
        url = SERVER_URL + url
        response = '''<xml>
                    <ToUserName><![CDATA[%s]]></ToUserName>
                    <FromUserName><![CDATA[%s]]></FromUserName>
                    <CreateTime>%s</CreateTime>
                    <MsgType><![CDATA[news]]></MsgType>
                    <ArticleCount>%s</ArticleCount>
                    <Articles>
                    <item>
                    <Title><![CDATA[%s]]></Title>
                    <Url><![CDATA[%s]]></Url>
                    <PicUrl><![CDATA[%s]]></PicUrl>
                    </item>
                    <item>
                    <Title><![CDATA[%s]]></Title>
                    <Url><![CDATA[%s]]></Url>
                    </item>
                    </Articles>
                    </xml>
                    '''% (msg['FromUserName'], msg['ToUserName'], str(int(time.time())), str(2), "您的个人信息列表", url, SERVER_URL+'/site_media/img/info_header.jpg', text, url)
        return_type = 'news'
        user.last_oper = 0
    elif eventKey == E_KEY_GRADE:
        response = "请选择新的年级:\n\r1.小学一年级\n\r2.小学二年级\n\r3.小学三年级\n\r4.小学四年级\n\r5.小学五年级\n\r6.小学六年级\n\r7.初中一年级\n\r8.初中二年级\n\r9.初中三年级\n\r10.高中一年级\n\r11.高中二年级\n\r12.高中三年级"
        user.last_oper = 400
    elif eventKey == E_KEY_PRODUCT:
        response = "闻题鸟微信服务号V1.0由一盆小铜钱小组为您敬上。了解更多我们的信息请致电15959542364。"
        user.last_oper = 0
    elif eventKey == E_KEY_FEEDBACK:
        response = "尊敬的用户您好，欢迎发送任何您的意见和建议:"
        user.last_oper = 500
    elif eventKey == E_KEY_ACTIVITY:
        response = "暂时没有活动信息哦，敬请期待我们接下来推出的活动。"
        user.last_oper = 0
    elif eventKey == E_KEY_DOWNLOAD:
        response = "App尚在开发中，敬请期待哟~"
        user.last_oper = 0
    else:
        #response = "Wrong Message Key!"
        exit(0)
    user.save()
    return response


def handle_voice(msg, user):
    response = ""
    if user.last_oper == 110:
        questionlist = Question.objects.filter(ques_owner=user.mmname, question_state='已选科')
        if len(questionlist) == 0:
            response = "未知的错误!请重新点击'我要提问'按钮开始提问"
            user.last_oper = 0
        else:
            media_id=msg.get("MediaId")
            path = STORE_PATH + media_id + '.' + msg.get("Format")
            download_file(media_id, path)
            question = questionlist[0]
            question.question_state = '待加图'
            question.ques_voice = "/site_media/files/"+media_id+'.'+msg.get("Format")
            question.content = msg.get("Recognition")
            question.save()
            response = "您要提的问题是：%s\n\r您还可以选择上传一张图片，也可直接回复任意文字消息结束本次提问。"%msg.get("Recognition")
            user.last_oper = 120
    elif user.last_oper == 200:
        name = get_user_name(user.mmname)
        content = msg.get("Recognition")
        question_bottle = QuestionBottle(ques_owner=user.mmname,owner_name=name,content=content,question_state='待解决',answer='',answer_name='')
        question_bottle.save()
        user.last_oper = 0
        response = "您的问题瓶已成功扔入大海，请静静等待有缘人吧~"
    elif user.last_oper == 300:
        content = msg.get("Recognition")
        question_bottle_list = QuestionBottle.objects.filter(id=user.ques_id)
        question_bottle = question_bottle_list[0]
        if question_bottle.question_state == '已解决':
            response = "已经有人在您之前将该问题解决了~再捡一个吧~"
            user.last_oper = 0
        else:
            question_bottle.answer = content
            answer_name = get_user_name(user.mmname)
            question_bottle.answer_name = answer_name
            question_bottle.question_state = "已解决"
            question_bottle.save()
            text = '您的问题瓶:%s\n\r已由用户:%s 解答，答案为：%s'%(question_bottle.content, question_bottle.answer_name, question_bottle.answer)
            post_message_text(question_bottle.ques_owner.encode('utf-8'), text.encode('utf-8'))
            user.last_oper = 0
            response = "用户%s已收到您的解答，谢谢您的热心解答~"%question_bottle.owner_name.encode('utf-8')
    else:
        response = "无效的操作，请继续上一步操作。"
    user.save()
    return response


def handle_picture(msg, user):
    response = ""
    if user.last_oper == 120:
        questionlist = Question.objects.filter(ques_owner=user.mmname, question_state='待加图')
        if len(questionlist) == 0:
            response = "未知的错误!请重新点击'我要提问'按钮开始提问"
            user.last_oper = 0
        else:
            media_id=msg.get("MediaId")
            path = STORE_PATH + media_id + '.jpg'
            download_file(media_id, path)
            question = questionlist[0]
            question.question_state = '待解决'
            question.ques_image = "/site_media/files/"+media_id+'.jpg'
            question.save()
            user.learncoin -= 2
            user.question_num += 1
            user.unsolved_num += 1
            response = "提问成功，半小时内将有老师为您解答，请耐心等待~"
            user.last_oper = 0
    else:
        response = "无效的操作，请继续上一步操作。"
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
        userlist = QBUser.objects.filter(mmname=mmname)
        questionlist = Question.objects.filter(ques_owner=mmname, question_state="已解决")
        return render_to_response('questionlist.html', {'questionlist': questionlist})
    else:
        html = "<html><body><h3>无效的访问!</h3></body></html>"
        return HttpResponse(html)


def unsolved(request):
    if request.method == "GET" and 'mmname' in request.GET:
        mmname = request.GET['mmname']
        userlist = QBUser.objects.filter(mmname=mmname)
        questionlist = Question.objects.filter(ques_owner=mmname, question_state="待解决")
        return render_to_response('questionlist.html', {'questionlist': questionlist})
    else:
        html = "<html><body><h3>无效的访问!</h3></body></html>"
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
    touser1 = 'oUJnEt_W6Z8wzIUgrXzIJlb1IEXI'
    touser2 = 'oUJnEt0yUGzq6qhbn7QjqQ_zDw-E'
    text = "Helloworld"
    # post_message_no_pic(touser.encode('utf-8'), text.encode('utf-8'), text.encode('utf-8'), 1)
    teacherlist = Teacher.objects.filter(teachername='xiaocw11')
    teacher = teacherlist[0]
    teacher.wealth += 5
    html = "<html><body><a href='http://www.baidu.com'>%d</a></body></html>"%teacher.id
    teacher.save()
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
        teachername = request.POST['teachername']
        password = request.POST['password']
        inviteNumber = request.POST['inviteNumber']
        school = request.POST['school']
        major = request.POST['major']
        email = request.POST['email']
        mobilenumber = request.POST['mobilenumber']
        number = RequestCode.objects.filter(request_code=inviteNumber)
        if len(number) == 0:
            return HttpResponse(simplejson.dumps({'state': 'invite'}), mimetype='application/json')
        subjects = request.POST.getlist('subjects')
        sublen = len(subjects)
        str = "";
        for i in subjects:
            str += i
        Teacherlist = Teacher.objects.filter(teachername=teachername)
        if len(Teacherlist) == 0:
            qbuser = Teacher(teachername=teachername, password=password, subjects=str, school=school, major=major,
                             email=email, mobilenumber=mobilenumber, wealth=0)
            qbuser.save()
            return HttpResponse(simplejson.dumps({"state": 'success'}), mimetype='application/json')
        else:
            return HttpResponse(simplejson.dumps({'state': 'existed'}), mimetype='application/json')
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
            unChineseQuestion1 = Question.objects.filter(category__contains="语文", question_state='待解决',question_changing=teacherid)
            unChineseQuestion2 = Question.objects.filter(category__contains="语文", question_state='待解决',question_changing=-1)
            unMathQuestion1 = Question.objects.filter(category__contains="数学", question_state='待解决', question_changing=teacherid)
            unMathQuestion2 = Question.objects.filter(category__contains="数学", question_state='待解决', question_changing=-1)
            unEnglishQuestion1 = Question.objects.filter(category__contains="英语", question_state='待解决',question_changing=teacherid)
            unEnglishQuestion2 = Question.objects.filter(category__contains="英语", question_state='待解决',question_changing=-1)
            resultUnsolved = []
            if chinese != -1:
                resultUnsolved += unChineseQuestion1
                resultUnsolved+=unChineseQuestion2
            if english != -1:
                resultUnsolved += unEnglishQuestion1
                resultUnsolved += unEnglishQuestion2
            if math != -1:
                resultUnsolved += unMathQuestion1
                resultUnsolved +=unMathQuestion2
            return render_to_response('questions_teacher.html',{'teachername': teacherlist[0].teachername, 'unsolve': resultUnsolved})
        else:
            return HttpResponseRedirect('/login_teacher/')
    else:
        html = "<html><body>None</body></html>"
        return HttpResponse(html)


def checkQuestion(request):
    if request.method == 'POST':
        questionid = request.POST["questionid"]
        question = Question.objects.filter(id=questionid)
        question = question[0]
        if question.question_changing < 0 or question.question_changing == request.session['teacherid']:
            question.question_changing = request.session['teacherid']
            question.start_time = time.strftime("%Y%m%d%H%M")
            question.save()
            return HttpResponse(simplejson.dumps({"state": 'success'}), mimetype='application/json')
        else:
            return HttpResponse(simplejson.dumps({"state": 'failed'}), mimetype='application/json')


@csrf_exempt
def answer(request):
    if request.method == 'POST':
        questionid = request.POST["id"]
        question = Question.objects.filter(id=questionid)
        question = question[0]
        currentTimes = time.strftime("%Y%m%d%H%M")
        dealTime = string.atoi(currentTimes) - string.atoi(question.start_time)
        if dealTime > 20L:
            question.question_changing = -1
            question.start_time = "0"
            question.save()
            return HttpResponse(simplejson.dumps({'state':'wrong'}), mimetype='application/json')
        if not request.POST.has_key('voice'):
            filename = time.strftime("%Y%m%d%H%M%S")
            file = request.FILES['voice']
            filename = filename + file.name[file.name.find('.'):]
            question.answer_voice = '/site_media' + '/files/' + filename[:-3] + "mp3"
            filename = STORE_PATH + filename
            destinaton = open(filename, 'wb')
            for chunk in file.chunks():
                destinaton.write(chunk)
            destinaton.close()
            assemble(filename)
        if not request.POST.has_key('image'):
            filename = time.strftime("%Y%m%d%H%M%S")
            file = request.FILES['image']
            filename = filename + file.name[file.name.find('.'):]
            question.answer_image = '/site_media' + '/files/' + filename
            filename = STORE_PATH + filename
            destinaton = open(filename, 'wb')
            for chunk in file.chunks():
                destinaton.write(chunk)
            destinaton.close()
        if request.POST['answerword']:
            question.answer = request.POST['answerword']
        question.solver_name = request.POST['solver']
        question.question_state = "已解决"
        question.answer_state = "待评分"
        question.start_time = currentTimes
        question.save()
        userlist = QBUser.objects.filter(mmname=question.ques_owner)
        user = userlist[0]
        if question.answer_image != '':
            url = SERVER_URL + question.answer_image
            post_message_pic(user.mmname.encode('utf-8'), url.encode('utf-8'), question.content.encode('utf-8'), question.answer.encode('utf-8'), question.id)
        else:
            post_message_no_pic(user.mmname.encode('utf-8'), question.content.encode('utf-8'), question.answer.encode('utf-8'), question.id)
        if question.answer_voice != '':
            url = SERVER_URL + question.answer_voice
            post_message_voice(user.mmname.encode('utf-8'), url.encode('utf-8'))
        text = "解答结束，请输入您对本次解答的评分(0或1分，0分不满意，1分表示满意)："
        post_message_text(user.mmname.encode('utf-8'), text.encode('utf-8'))
        user.last_oper = 600
        user.unsolved_num -= 1
        user.save()
        return HttpResponse(simplejson.dumps({"state": 'success'}),mimetype='application/json')


def questions_unEvaluate(request):
    if request.method == 'GET':
        if request.session.has_key('teacherid'):
            teacherid = request.session['teacherid']
            teacherlist = Teacher.objects.filter(id=teacherid)
            unEvaluate = Question.objects.filter(solver_name=teacherlist[0].teachername, answer_satis=0)
            return render_to_response('question_unEvaluate.html',{'teachername': teacherlist[0].teachername, 'teacherid': teacherid,'unEvaluate': unEvaluate})
        else:
            HttpResponseRedirect('/login_teacher')
    else:
        html = "<html><body>None</body></html>"
        return HttpResponse(html)

def replayQuestion(request):
    if request.method == 'POST':
        currentTimes = time.strftime("%Y%m%d%H%M")
        questionid = request.POST["id"]
        question = Question.objects.filter(id=questionid)
        question = question[0]
        if not request.POST.has_key('voice'):
            filename = time.strftime("%Y%m%d%H%M%S")
            file = request.FILES['voice']
            filename = filename + file.name[file.name.find('.'):]
            question.answer_voice = '/site_media' + '/files/' + filename
            filename = STORE_PATH + filename
            destinaton = open(filename, 'wb')
            for chunk in file.chunks():
                destinaton.write(chunk)
            destinaton.close()
        elif not request.POST.has_key('image'):
            filename = time.strftime("%Y%m%d%H%M%S")
            file = request.FILES['image']
            filename = filename + file.name[file.name.find('.'):]
            question.answer_image = '/site_media' + '/files/' + filename
            filename = STORE_PATH + filename
            destinaton = open(filename, 'wb')
            for chunk in file.chunks():
                destinaton.write(chunk)
            destinaton.close()
        if request.POST['answerword']:
            question.answer = request.POST['answerword']
        question.solver_name = request.POST['solver']
        question.question_state = "已解决"
        question.answer_state = "待评分"
        question.start_time = currentTimes
        question.save()
        userlist = QBUser.objects.filter(mmname=question.ques_owner)
        user = userlist[0]
        if question.answer_image != '':
            url = SERVER_URL + question.answer_image
            post_message_pic(user.mmname.encode('utf-8'), url.encode('utf-8'), question.content.encode('utf-8'), question.answer.encode('utf-8'), question.id)
        else:
            post_message_no_pic(user.mmname.encode('utf-8'), question.content.encode('utf-8'), question.answer.encode('utf-8'), question.id)
        if question.answer_voice != '':
            url = SERVER_URL + question.answer_voice
            post_message_voice(user.mmname.encode('utf-8'), url.encode('utf-8'))
        text = "解答结束，请输入您对本次解答的评分(0或1分，0分不满意，1分表示满意)："
        post_message_text(user.mmname.encode('utf-8'), text.encode('utf-8'))
        user.last_oper = 600
        user.save()
        return HttpResponse(simplejson.dumps({'state': 'success'}), mimetype='application/json')

def questions_solved(request):
     if request.method == 'GET':
        if request.session.has_key('teacherid'):
            teacherid = request.session['teacherid']
            teacherlist = Teacher.objects.filter(id=teacherid)
            resultSolved = Question.objects.filter(solver_name=teacherlist[0].teachername,answer_satis = 1)
            return render_to_response('questions_solved.html',{'teachername':teacherlist[0].teachername,'solve':resultSolved})
        else:
        	return HttpResponseRedirect('/login_teacher/')

def profile_teacher(request):
    if request.method =='GET':
        if request.session.has_key('teacherid'):
            teacherid = request.session['teacherid']
            teacherlist = Teacher.objects.filter(id=teacherid)
            if len(teacherlist) == 0:
                return HttpResponseRedirect('/login_teacher/')
            teacher = teacherlist[0]
            chinese = teacher.subjects.find('chinese')
            english = teacher.subjects.find('english')
            math = teacher.subjects.find('math')
            if chinese != -1:
                chinese = True
            else:
                chinese = False
            if english != -1:
                english = True
            else:
                english = False
            if math != -1:
                math = True
            else:
                math = False
            return render_to_response('profile_teacher.html',{'teacher':teacher,'chinese':chinese,'english':english,'math':math})
        else:
            return HttpResponseRedirect('/login_teacher/')
    elif request.method == "POST":
        if request.session.has_key('teacherid'):
            teacherid = request.session['teacherid']
            teacherlist = Teacher.objects.filter(id=teacherid)
            if len(teacherlist) == 0:
                return HttpResponseRedirect('/login_teacher/')
            teacher = teacherlist[0]
            if request.POST['submittype'] == "0":
                password = request.POST['password']
                teacher.password = password
                teacher.save()
            else:
                school = request.POST['school']
                major  = request.POST['major']
                email = request.POST['email']
                mobilenumber = request.POST['mobilenumber']
                subjects = request.POST.getlist('subjects')
                sublen = len(subjects)
                str = "";
                for i in subjects:
                    str += i
                teacher.school = school
                teacher.major = major
                teacher.email = email
                teacher.mobilenumber = mobilenumber
                teacher.subjects = str
                teacher.save()
            chinese = teacher.subjects.find('chinese')
            english = teacher.subjects.find('english')
            math = teacher.subjects.find('math')
            if chinese != -1:
                chinese = True
            else:
                chinese = False
            if english != -1:
                english = True
            else:
                english = False
            if math != -1:
                math = True
            else:
                math = False
            return HttpResponse(simplejson.dumps({"state":'success'}),mimetype='application/json')
        else:
            return HttpResponse(simplejson.dumps({"state":'error'}),mimetype='application/json')
    else:
        html = "<html><body>None</body></html>"
        return HttpResponse(html)


def exchange_teacher(request):
    if request.method =='GET':
        if request.session.has_key('teacherid'):
            teacherid = request.session['teacherid']
            teacherlist = Teacher.objects.filter(id=teacherid)
            if len(teacherlist) == 0:
                return HttpResponseRedirect('/login_teacher/')
            teacher = teacherlist[0]
            return render_to_response('exchange_teacher.html',{'teacher':teacher})
        else:
            return HttpResponseRedirect('/login_teacher/')
    elif request.method == "POST":
        if request.session.has_key('teacherid'):
            teacherid = request.session['teacherid']
            teacherlist = Teacher.objects.filter(id=teacherid)
            if len(teacherlist) == 0:
                return HttpResponseRedirect('/login_teacher/')
            teacher = teacherlist[0]
            #发邮件
            mailto_list=["470385822@qq.com"]
            mail_host="smtp.qq.com"  #设置服务器
            mail_user="2529705770"    #用户名
            mail_pass="zst1409"   #口令
            mail_postfix="qq.com"  #发件箱的后缀
            me="hello"+"<"+mail_user+"@"+mail_postfix+">"
            if request.POST['submittype'] == "0" and teacher.wealth >= 50:
            	cardname="50元充值卡"
            elif request.POST['submittype'] == "1" and teacher.wealth >= 100:
            	cardname="100元充值卡"
            content = teacher.teachername + "订购了一个" + cardname + "\n联系电话：" + teacher.mobilenumber + "\n邮箱：" + teacher.email
            msg = MIMEText(content,_subtype='plain',_charset='gb2312')
            msg['Subject'] = "新的订单"
            msg['From'] = me
            msg['To'] = ";".join(mailto_list)
            try:
                server = smtplib.SMTP()
                server.connect(mail_host)
                server.login(mail_user,mail_pass)
                server.sendmail(me, mailto_list, msg.as_string())
                server.close()
                if request.POST['submittype'] == "0" and teacher.wealth >= 50:
                    teacher.wealth = teacher.wealth - 50
                elif request.POST['submittype'] == "1" and teacher.wealth >= 100:
                    teacher.wealth = teacher.wealth - 100
                teacher.save()
                return HttpResponse(simplejson.dumps({"state":'success'}),mimetype='application/json')
            except Exception, e:
                return HttpResponse(simplejson.dumps({"state":'error'}),mimetype='application/json')
        else:
            return HttpResponse(simplejson.dumps({"state":'nologin'}),mimetype='application/json')
    else:
        html = "<html><body>None</body></html>"
        return HttpResponse(html)


def logout_teacher(request):
    if request.method == "GET":
        request.session.flush()
        return render_to_response('login_teacher.html')
    else:
        return render_to_response('login_teacher.html')


def assemble(filename): 
    lamepath = "F:\\lame\\lame.exe" 
    dquotaion="\""  
    space=" "  
    slash="\\"  
    quality="-h -V 0 --preset insane"  
    lamepath = lamepath  
    filewav = dquotaion+filename+dquotaion  
    filemp3 = dquotaion+filename[:-3]+"mp3"+dquotaion  
    command = lamepath+space+quality+space+filewav+space+filemp3  
    os.popen(command)


def single_question(request):
    if request.method =='GET' and 'id' in request.GET:
        ques_id = request.GET['id']
        questionlist = Question.objects.filter(id=ques_id)
        question = questionlist[0]
        return render_to_response('que.html', {'question': question})
    else:
        html = "<html><body><h3>无效的访问!</h3></body></html>"
        return HttpResponse(html)


def user_info(request):
    if request.method =='GET' and 'mmname' in request.GET:
        mmname = request.GET['mmname']
        userlist = QBUser.objects.filter(mmname=mmname)
        user = userlist[0]
        return render_to_response('user_info.html', {'user': user})
    else:
        html = "<html><body><h3>无效的访问!</h3></body></html>"
        return HttpResponse(html)


def not_found(request):
    return render_to_response('404.html')