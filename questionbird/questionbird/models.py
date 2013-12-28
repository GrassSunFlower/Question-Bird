#! /usr/bin/env python
# coding=utf-8
from django.db import models



class Question(models.Model):
    #问题的发起人，这里使用的是闻题鸟的账号
    ques_owner = models.CharField(max_length=50)
    #问题的内容
    content = models.CharField(max_length=200)
    #问题中的图片
    ques_image = models.CharField(max_length=200)
    #问题中的语音
    ques_voice = models.CharField(max_length=200)
    #问题的科目分类
    category = models.CharField(max_length=30)
    #问题的状态：已解决或待解决
    question_state = models.CharField(max_length=10)
    #问题正在改变
    question_changing = models.IntegerField(max_length=10)
    #回答内容
    answer = models.CharField(max_length=100)
    #回答中的图片
    answer_image = models.CharField(max_length=200)
    #回答中的语音
    answer_voice = models.CharField(max_length=200)
    #回答的状态：已评价或未评价
    answer_state = models.CharField(max_length=10)
    #回答的满意度
    answer_satis = models.IntegerField()
    #回答的评价
    answer_eva = models.CharField(max_length=20)
    #回答教师的名字
    solver_name = models.CharField(max_length=50)
    #问题回答的起始时间
    start_time= models.CharField(max_length=20)
    #问题回答时间:
    answer_time = models.CharField(max_length = 20)


class QBUser(models.Model):
    # QuestionBird name 闻题鸟用户名，即微信openID
    mmname = models.CharField(max_length=50)
    # 剩余学习币
    learncoin = models.IntegerField()
    # 已提问次数
    question_num = models.IntegerField()
    # 待解决问题数
    unsolved_num = models.IntegerField()
    # 年级
    grade = models.CharField(max_length=30)
    # 最后的操作
    last_oper = models.IntegerField()
    # 捡到的问题id
    ques_id = models.IntegerField()

# 漂流瓶问题
class QuestionBottle(models.Model):
    # 问题的发起人，这里使用的是闻题鸟的账号
    ques_owner = models.CharField(max_length=50)
    # 用户名
    owner_name = models.CharField(max_length=50)
    # 问题的内容
    content = models.CharField(max_length=200)
    # 问题的状态：已解决或待解决
    question_state = models.CharField(max_length=10)
    # 回答内容
    answer = models.CharField(max_length=100)
    # 回答者名字
    answer_name = models.CharField(max_length=50)


class Suggestion(models.Model):
    #建议内容
    content = models.CharField(max_length=100)

class Teacher(models.Model):
    #QuestionBird教师用户名
    teachername = models.CharField(max_length=50)
    #教师密码
    password = models.CharField(max_length=30)
    #教师擅长学科
    subjects = models.CharField(max_length=100)
    #教师学校
    school = models.CharField(max_length=30)
    #教师专业
    major = models.CharField(max_length=30)
    #教师邮箱
    email = models.CharField(max_length=30)
    #教师电话
    mobilenumber = models.CharField(max_length=30)
    #教师财富值
    wealth = models.IntegerField()


class RequestCode(models.Model):
    #邀请码
    request_code = models.CharField(max_length=30)