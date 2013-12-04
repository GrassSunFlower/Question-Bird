#! /usr/bin/env python
# coding=utf-8

#token值
QB_TOKEN = "questionbird"
#返回类型,默认为文本信息
RET_TYPE = "text"

#登陆、注册、登出操作的eventkey值
E_KEY_LOGIN = "Q_login_regis_logout"
#提出问题的eventkey值
E_KEY_ASK = "Q_ask_ques"
#查看已解决的问题的eventkey值
E_KEY_SOLVED = "Q_solved_ques"
#查看待解决的问题的eventkey值
E_KEY_UNSOLVED = "Q_unsolved_ques"

CATEGORY_DIC = {
	'1' : '小学语文',
	'2' : '小学数学',
	'3' : '初中语文',
	'4' : '初中数学',
	'5' : '初中英语',
	'6' : '高中语文',
	'7' : '高中数学',
	'8' : '高中英语',
}