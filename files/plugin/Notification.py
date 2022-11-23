# coding=utf-8
import time, os


class Notice:
    def __init__(self):
        print(f'====>> 通知机器人初始化')
        pass

    def notice_ding_talk(self, webhook: str, content: str):
        print(f'正在发送钉钉机器人通知====>>>\n{content}')
        if webhook is None:
            webhook = WebHook.url_ding_talk_bot
        if content is None:
            raise Exception('content cant be None!')
        command = f'curl \'{webhook}\' -H \'Content-Type: application/json\' -d \'{content}\''
        print(os.system(command))
        pass

    def notice_wechat(self, webhook: str = None, content: str = None):
        print(f'正在发送微信机器人通知====>>>\n{content}')
        if webhook is None:
            webhook = WebHook.url_wechat_bot
        if content is None:
            raise Exception('content cant be None!')
        command = f'curl \'{webhook}\' -H \'Content-Type: application/json\' -d \'{content}\''
        print(os.system(command))
        pass

    @staticmethod
    def build_content(wechat: bool, base_apk: bool, file: str, package: str, app_name: str, version: str, jiagu: bool, sign: bool, log: str, others: str = None):
        """
        钉钉格式 '{"msgtype": "markdown","markdown":{"text":"markdown"}}'
        微信格式 '{"msgtype": "markdown","markdown":{"content":"markdown"}}'
        :return:
        """
        base_ = '{"msgtype": "markdown","markdown":{"title":"马甲包打包通知","text":"contentstr"}}'
        if wechat:
            base_ = base_.replace("text", "content")
        # print(base_)
        content = f'马甲包构建脚本执行完成！包相关信息如下：' \
                  f'\n> - 包类型：{"基准包" if base_apk else "推广包"}' \
                  f'\n> - 文件名：{file}' \
                  f'\n> - 包名： {package}' \
                  f'\n> - 应用名： {app_name}' \
                  f'\n> - 版本号：{version}' \
                  f'\n> - 加固状态：{"易盾加固" if jiagu else "未加固"}' \
                  f'\n> - 签名：{"已签名" if sign else "未签名"}' \
                  f'\n> - 构建时间：{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}' \
                  f'\n> - 备注：{others}'
        # 固定外网访问
        content = f'{content}\n>\n> [源apk文件下载](http:zhouqipa.cn/files/apks/{file})'
        if log is not None and len(log) > 0 and 'data' in log:
            content = f'{content}\n> [源log文件下载](http:zhouqipa.cn{log.replace("data", "files")})'
        # print(content)
        return base_.replace('contentstr', content)
        pass


class WebHook:
    url_ding_talk_bot = 'https://oapi.dingtalk.com/robot/send?access_token=aeb3d5dcbc73e6a75a3c3fd4dd139e92ecb0ecdb4133772312e430c4c8fb64ce'
    url_wechat_bot = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=5172ea61-5097-430a-97c8-c84ced604cd2'
