import os
import json
import yagmail


class EmailSender:
    def __init__(self, conf_path: str):
        if not os.path.exists(conf_path):
            print(f"[error][邮件服务器配置文件不存在]")
            return

        with open(conf_path, 'r', encoding='utf-8') as f:
            d = json.load(f)
            # 邮件服务器地址
            self.server = d["server"]
            # 邮件服务器端口
            self.server_port = d["server_port"]
            # 发件人邮箱
            self.sender = d["sender"]
            # 发件人秘钥
            self.sender_key = d["sender_key"]

    def check(self):
        return (self.server is not None) and (self.server_port is not None) and (self.sender is not None) and \
               (self.sender_key is not None)

    def send_email(self, receiver: str, subject: str, text: str):
        """
        发送邮件
        :param receiver: 收件人邮箱地址
        :param subject: 邮件主题
        :param text: 邮件正文
        :return: None
        """
        if not self.check():
            return

        yag = yagmail.SMTP(user=self.sender, password=self.sender_key, host=self.server, port=self.server_port)
        contents = [text]
        yag.send(receiver, subject, contents)
        yag.close()

        print(f"[{receiver}] [发送成功]")
