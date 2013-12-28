#! /usr/bin/env python
# coding=utf-8

#运行的服务器网址
SERVER_URL= "http://59.66.149.157"
#token值
QB_TOKEN = "questionbird"
#AppId值 在微信公共平台管理页获得
APP_ID = "wx2a405d14abedb32c"
#AppSecret值 在微信公共平台管理页获得
APP_SECRET = "a4ddbe11cf22ceac471e10bfb8de3836"
#获取access_token的url
ACCESS_URL = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s"
#图片储存路径
STORE_PATH = 'F:\\pythonproject\\questionbird\\static\\files\\'
#上传url
UPLOAD_URL = 'http://file.api.weixin.qq.com/cgi-bin/media/upload?access_token=%s&type=%s'
#下载url
DOWNLOAD_URL = 'http://file.api.weixin.qq.com/cgi-bin/media/get?access_token=%s&media_id=%s'
#主动发送消息post的url
POST_URL = 'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=%s'
#获取用户名的get的url
GET_NAME_URL = 'https://api.weixin.qq.com/cgi-bin/user/info?access_token=%s&openid=%s'

# 提出问题的eventkey值
E_KEY_ASK = "Q_ask_ques"
# 查看已解决的问题的eventkey值
E_KEY_SOLVED = "Q_solved_ques"
# 查看待解决的问题的eventkey值
E_KEY_UNSOLVED = "Q_unsolved_ques"
# 扔一个
E_KEY_THROW = "Q_raise_ques"
# 捡一个
E_KEY_PICK = "Q_pick_ques"
# 查看资料的eventkey值
E_KEY_INFO = "Q_information"
# 更改年级的eventkey值
E_KEY_GRADE = "Q_chg_grade"
# 产品信息的eventkey值
E_KEY_PRODUCT = "Q_product_info"
# 反馈意见的eventkey值
E_KEY_FEEDBACK = "Q_feedback"
# 查看活动的eventkey值
E_KEY_ACTIVITY = "Q_activity"
# 下载App的eventkey值
E_KEY_DOWNLOAD = "Q_download"

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

CATEGORY_GRADE_DIC = {
	'1' : '小学一年级',
	'2' : '小学二年级',
	'3' : '小学三年级',
	'4' : '小学四年级',
	'5' : '小学五年级',
	'6' : '小学六年级',
	'7' : '初中一年级',
	'8' : '初中二年级',
	'9' : '初中三年级',
	'10': '高中一年级',
	'11': '高中二年级',
	'12': '高中三年级',
}

ANSWER_SCORE = {
	'0' : 0,
	'1' : 1,
}