#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
平安行动自动打卡

请事先安装好 lxml 和 requests 模块

    pip install lxml requests yagmail

然后修改 26-29 行为自己的数据，如有需要请自行配置 161-184 行的 SMTP 发信

Created on 2020-04-13 20:20
@author: ZhangJiawei & Monst.x
@author: Liu Chongpeng & Liu Lu
"""

import json
import os
import random
import re
import sys
import time
import traceback

import lxml.html
import requests
from myEmail import EmailSender

# 改变工作路径为当前文件所在路径
os.chdir(os.path.dirname(sys.argv[0]))
"""
请在config.json中填写相应信息
my_id: 学号
my_pass: 统一认证密码
my_bound: 获取方式见原作者blog：https://blog.monsterx.cn/code/heu-auto-checkin-covid19/
my_data: 同上。注意，直接在json中粘贴字典即ok，下边统一转字符串
"""
with open("config.json", "r", encoding="utf-8") as f:
    info_data = json.load(f)
    my_id = info_data["myid"]
    my_pass = info_data["mypass"]
    my_bound = info_data["mybound"]
    # 这玩意原本是字典，用json库给dumps成字符串
    my_data = json.dumps(info_data["mydata"])
    # 收件人地址
    email_receiver = info_data["receiver"]

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    # "Content-Type": "application/x-www-form-urlencoded",
    "Cookie": "",
    "Host": "cas.hrbeu.edu.cn",
    "Origin": "https://cas.hrbeu.edu.cn",
    "Referer": "https://cas.hrbeu.edu.cn/cas/login",

    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.74"
}

data = {
    "username": my_id,  # 学号
    "password": my_pass  # 教务处密码
}


def findStr(source, target):
    return source.find(target) != -1


# 这些是提示变量，无需设置初值
title = ""
msg = ""
proxies = {"http": None, "https": None}
success = True

if __name__ == '__main__':
    try:
        # get
        url_login = 'https://cas.hrbeu.edu.cn/cas/login'
        print("============================\n[debug] Begin to login ...")
        sesh = requests.session()
        req = sesh.get(url_login, proxies=proxies)
        html_content = req.text

        # post
        login_html = lxml.html.fromstring(html_content)

        # cookie acquire

        hidden_inputs = login_html.xpath(
            r'//input[@type="hidden" and @class="for-form"]')
        user_form = {x.attrib["name"]: x.attrib["value"]
                     for x in hidden_inputs}

        if user_form['pid'] == '':
            user_form.pop('pid')

        user_form["username"] = data['username']
        user_form["password"] = data['password']
        # user_form["captcha"] = ''
        user_form["_eventId"] = 'submit'

        # headers['Cookie'] = headers['Cookie'] + req.headers['Set-cookie']
        headers['Cookie'] = headers['Cookie'] + req.headers['Set-cookie'].split(' ')[0] + req.headers['Set-cookie'].split(' ')[3]

        # print(req.headers['Set-cookie'])
        # print(req.headers['Set-cookie'].split(' ')[0])
        # print(req.headers['Set-cookie'].split(' ')[3])

        headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75"
        req.url = f'https://cas.hrbeu.edu.cn/cas/login'

        tmp_headers = headers.copy()
        tmp_headers['Cookie'] = tmp_headers['Cookie'] + req.headers['Set-cookie']

        sesh.get("https://cas.hrbeu.edu.cn/cas/resources/E7rD9PrgTl/static/css/modules/login.2804a2c6afaaea5b748615e8962b652a.css?e72b994e962819eb795d",
                 headers=headers, proxies=proxies)
        sesh.get("https://cas.hrbeu.edu.cn/cas/resources/E7rD9PrgTl/static/js/modules/login.3ca4faf6f3c2c795ec39.js?e72b994e962819eb795d",
                 headers=headers, proxies=proxies)
        sesh.get("https://cas.hrbeu.edu.cn/cas/resources/E7rD9PrgTl/static/source/dingtalk.open.js",
                 headers=headers, proxies=proxies)

        response302 = sesh.post(req.url, data=user_form,
                                headers=headers, proxies=proxies)

        tmp_headers['Cookie'] = tmp_headers['Cookie'] + \
            req.headers['Set-cookie']
        sesh.get("https://cas.hrbeu.edu.cn/cas/resources/E7rD9PrgTl/static/css/modules/success.e7a71379e2a00fe3633da1d6d69ef866.css?e72b994e962819eb795d=",
                 headers=tmp_headers, proxies=proxies)
        sesh.get("https://cas.hrbeu.edu.cn/cas/resources/E7rD9PrgTl/static/js/modules/success.1f12e1b1e088cb52e798.js?e72b994e962819eb795d=",
                 headers=tmp_headers, proxies=proxies)

        response302 = sesh.get(req.url, data=user_form,
                                headers=headers, proxies=proxies)
        # casRes = response302.history[0]
        # print("[debug] CAS response header", findStr(casRes.headers['Set-Cookie'], 'CASTGC'))

        # print("################")
        # print(html_content)
        # print(user_form)
        # print(response302.request)
        # print(response302.request.headers)
        # print(response302.headers)
        # print(response302.text)
        # time.sleep(2)

        # get
        jkgc_response = sesh.get(
            "http://jkgc.hrbeu.edu.cn/infoplus/form/JSXNYQSBtest/start", proxies=proxies)
        jkgc_response = sesh.get(
            "http://jkgc.hrbeu.edu.cn/infoplus/form/JSXNYQSBtest/start", proxies=proxies)

        # print("#########")
        # print(jkgc_response.headers)
        # print(jkgc_response.text)
        
        # post
        headers['Accept'] = '*/*'
        headers['Cookie'] = jkgc_response.request.headers['Cookie']
        headers['Host'] = 'jkgc.hrbeu.edu.cn'
        headers['Referer'] = jkgc_response.url
        jkgc_html = lxml.html.fromstring(jkgc_response.text)
        csrfToken = jkgc_html.xpath(r'//meta[@itemscope="csrfToken"]')
        csrfToken = csrfToken.pop().attrib["content"]
        jkgc_form = {
            'idc': 'JSXNYQSBtest',
            'release': '',
            'csrfToken': csrfToken,
            'formData': {
                '_VAR_URL': jkgc_response.url,
                "_VAR_URL_Attr": {}
            }
        }
        jkgc_form['formData'] = json.dumps(jkgc_form['formData'])
        jkgc_url = 'http://jkgc.hrbeu.edu.cn/infoplus/interface/start'
        response3 = sesh.post(jkgc_url, data=jkgc_form,
                              headers=headers, proxies=proxies)

        # get
        form_url = json.loads(response3.text)['entities'][0]
        form_response = sesh.get(form_url)

        # post
        headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        headers['Referer'] = form_url
        headers['X-Requested-With'] = 'XMLHttpRequest'
        submit_url = 'http://jkgc.hrbeu.edu.cn/infoplus/interface/doAction'

        submit_html = lxml.html.fromstring(form_response.text)
        csrfToken2 = submit_html.xpath(r'//meta[@itemscope="csrfToken"]')
        csrfToken2 = csrfToken2.pop().attrib["content"]

        submit_form = {
            'actionId': '1',
            # boundFields 修改位置
            'boundFields': my_bound,
            'csrfToken': csrfToken2,
            # formData 修改位置
            'formData': my_data,
            'lang': 'zh',
            'nextUsers': '{}',
            'rand': str(random.random() * 999),
            'remark': '',
            'stepId': re.match(r'.*form/(\d*?)/', form_response.url).group(1),
            'timestamp': str(int(time.time() + 0.5))
        }
        response_end = sesh.post(
            submit_url, data=submit_form, headers=headers, proxies=proxies)
        resJson = json.loads(response_end.text)

        # 表单填写完成，返回结果
        # print('[debug] Form url: ', form_response.url)
        # print('Form status: ', response_end.text)
        print('[debug] Form Status: ', resJson['ecode'])
        print('[debug] Form stJson: ', resJson)
        # 获取表单返回 Json 数据所有 key 用这个
        # print('Form stJsonkey: ', resJson.keys())

        if (resJson['errno'] == 0):
            print('[info] Checkin succeed with jsoncode', resJson['ecode'])
            title = f'打卡成功 <{submit_form["stepId"]}>'
            msg = '\t表单地址: ' + form_response.url + '\n\n\t表单状态: \n\t\terrno：' + str(
                resJson['errno']) + '\n\t\tecode：' + str(resJson['ecode']) + '\n\t\tentities：' + str(
                resJson['entities']) + '\n\n\n\t完整返回：' + response_end.text
        else:
            print('[error] Checkin error with jsoncode', resJson['ecode'])
            title = f'打卡失败！校网出错'
            msg = '\t表单地址: ' + form_response.url + '\n\n\t错误信息: \n\t\terrno：' + str(
                resJson['errno']) + '\n\t\tecode：' + str(resJson['ecode']) + '\n\t\tentities：' + str(
                resJson['entities']) + '\n\n\n\t完整返回：' + response_end.text
    except:
        success = False
        print('\n[error] :.:.:.:.: Except return :.:.:.:.:')
        err = traceback.format_exc()
        print('[error] Python Error: \n', err)
        title = '打卡失败！脚本出错'
        msg = '\t脚本报错: \n\n\t' + err + '============================\n'
    finally:
        print(':.:.:.:.: Finally :.:.:.:.:')

        subject = "平安行动 打卡成功" if success else "平安行动 打卡失败！"
        sender = EmailSender(conf_path="./config.json")

        if email_receiver is not "" and sender.check():
            sender.send_email(
                receiver=email_receiver,
                subject=subject,
                text="邮件自动生成, 无需回复"
            )

        print('[info] Task Finished at', time.strftime(
            "%Y-%m-%d %H:%M:%S %A", time.localtime()))
        print('============================\n')
