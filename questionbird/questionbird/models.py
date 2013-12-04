#! /usr/bin/env python
# coding=utf-8
from django.db import models

class User(models.Model):
	#MicroMessage name 微信名
	mmname = models.CharField(max_length = 50)
	#QuestionBird name 闻题鸟用户名
	qbname = models.CharField(max_length = 50)
    #闻题鸟密码
	password = models.CharField(max_length = 30)
    #最后的操作
	last_oper = models.IntegerField()


class Question(models.Model):
    #问题的发起人，这里使用的是闻题鸟的账号
    ques_owner = models.CharField(max_length = 50)
    #问题的内容
    content = models.CharField(max_length = 200)
    #问题的科目分类
    category = models.CharField(max_length = 30)
    #问题的状态：已解决或待解决
    question_state = models.CharField(max_length = 10)
    #回答
    answer = models.CharField(max_length = 100)
    #回答的状态：已评价或未评价
    answer_state = models.CharField(max_length = 10)
    #回答的满意度
    answer_satis = models.CharField(max_length = 10)
    #回答的评价
    answer_eva = models.CharField(max_length = 20)
    #回答教师的名字
    solver_name = models.CharField(max_length = 50)


class QBUser(models.Model):
	#QuestionBird name 闻题鸟用户名
	qbname = models.CharField(max_length = 50)
    #闻题鸟密码
	password = models.CharField(max_length = 30)
