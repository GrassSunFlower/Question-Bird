# encoding: utf-8

# author hzlzh
# must be python 2.x

import json
import urllib
import urllib2

appid = "wx2a405d14abedb32c"
secret = "a4ddbe11cf22ceac471e10bfb8de3836"
access_url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s"
menu_url = "https://api.weixin.qq.com/cgi-bin/menu/create?%s"


def get_access_token():
    f = urllib.urlopen(access_url % (appid, secret))
    resp = json.loads(f.read())
    print resp
    return resp['access_token']


def generate_menu(token):
    menus = {
        "button": [
            {
                "name": "我的账号",
                "sub_button":[
                {
                    "type": "click",
                    "name": "查看资料",
                    "key": "Q_information"
                },
                {
                    "type": "click",
                    "name": "更改昵称",
                    "key": "Q_chg_name"
                },
                {
                    "type": "click",
                    "name": "更改密码",
                    "key": "Q_chg_pass"
                },
                {
                    "type": "click",
                    "name": "更改年级",
                    "key": "Q_chg_grade"
                },
                {
                    "type": "click",
                    "name": "登陆/注册/登出",
                    "key": "Q_login_regis_logout"
                }]
            },
            {
                "name": "我的问题",
                "sub_button":[
                {
                    "type": "click",
                    "name": "我要提问",
                    "key": "Q_ask_ques"
                },
                {
                    "type": "click",
                    "name": "已解决问题",
                    "key": "Q_solved_ques"
                },
                {
                    "type": "click",
                    "name": "待解决问题",
                    "key": "Q_unsolved_ques"
                },
                {
                    "type": "click",
                    "name": "搜索问题",
                    "key": "Q_serch_ques"
                }]
            },
            {
                "name": "关于我们",
                "sub_button":[
                {
                    "type": "click",
                    "name": "产品信息",
                    "key": "Q_product_info"
                },
                {
                    "type": "click",
                    "name": "反馈意见",
                    "key": "Q_feedback"
                },
                {
                    "type": "click",
                    "name": "查看活动",
                    "key": "Q_activity"
                }]
            }]
    }
    params = {'access_token': urllib.quote(token)}
    url = menu_url % urllib.urlencode(params)
    request = urllib2.Request(url, json.dumps(menus, ensure_ascii=False))
    response = urllib2.urlopen(request)
    print response.read()


def main():
    token = get_access_token()
    generate_menu(token)


if __name__ == '__main__':
    main()