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
    askname = models.CharField(max_length = 50)
    content = models.CharField(max_length = 100)
    category = models.CharField(max_length = 30)
    state = models.IntegerField()
    answer = models.CharField(max_length = 100)
    answername = models.CharField(max_length = 50)
