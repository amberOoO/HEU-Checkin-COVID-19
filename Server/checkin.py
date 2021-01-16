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
import random
import re
import time
import traceback

import lxml.html
import requests
from myEmail import EmailSender

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
    "Accept-Language": "zh-CN",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "Cookie": "MESSAGE_TICKET=%7B%22times%22%3A0%7D; ",
    "Host": "cas.hrbeu.edu.cn",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18362"
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
        url_login = 'https://cas.hrbeu.edu.cn/cas/login?'
        print("============================\n[debug] Begin to login ...")
        sesh = requests.session()
        req = sesh.get(url_login, proxies=proxies)
        html_content = req.text

        # post
        login_html = lxml.html.fromstring(html_content)
        hidden_inputs = login_html.xpath(r'//div[@id="main"]//input[@type="hidden"]')
        user_form = {x.attrib["name"]: x.attrib["value"] for x in hidden_inputs}

        user_form["username"] = data['username']
        user_form["password"] = data['password']
        user_form["captcha"] = ''
        user_form["submit"] = '登 录'
        headers['Cookie'] = headers['Cookie'] + req.headers['Set-cookie']
        headers[
            'User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75"
        req.url = f'https://cas.hrbeu.edu.cn/cas/login'
        response302 = sesh.post(req.url, data=user_form, headers=headers, proxies=proxies)
        # casRes = response302.history[0]
        # print("[debug] CAS response header", findStr(casRes.headers['Set-Cookie'], 'CASTGC'))

        # get
        jkgc_response = sesh.get("http://jkgc.hrbeu.edu.cn/infoplus/form/JSXNYQSBtest/start", proxies=proxies)
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
        response3 = sesh.post(jkgc_url, data=jkgc_form, headers=headers, proxies=proxies)

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
        response_end = sesh.post(submit_url, data=submit_form, headers=headers, proxies=proxies)
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

        print('[info] Task Finished at', time.strftime("%Y-%m-%d %H:%M:%S %A", time.localtime()))
        print('============================\n')
