# coding=utf-8
import datetime
import os, constants, sys
from files.plugin.FilePlugin import FilePlugin
from files.plugin.git import Git
from files.sign.Sign import *
from files.ydjiagu.YDJiagu import *
from files.plugin.JKSPlugin import *
from files.plugin.Notification import *


class Entry:

    @staticmethod
    def reset_properties():
        local_properties = '/root/sung/android/project/huajian-android/local.properties'
        sdk_dir = '/usr/local/android/android-sdk'
        ndk_dir = os.path.join(sdk_dir, 'ndk/android-ndk-r21e')
        if not os.path.exists(local_properties):
            os.mknod(local_properties)
        else:
            print(f'local.properties 文件存在,跳过创建修改')
            return
        file_content = f'sdk.dir = {sdk_dir}\nndk.dir = {ndk_dir}'
        FilePlugin.wirte_str_to_file(file_content, local_properties)
        print(f'local.properties 创建成功')
        pass

    @staticmethod
    def rollback():
        git = Git(constants.path_android)
        git.remove_local_change()
        pass

    @staticmethod
    def pull_origin_code(branch: str):
        git = Git(constants.path_android)
        git.remove_local_change()
        git.pull_(branch)
        pass

    @staticmethod
    def gradle_clean():
        Entry.reset_properties()
        os.chdir(constants.path_android)
        print(os.system("gradle clean"))
        pass

    @staticmethod
    def release_apk():
        os.chdir(constants.path_self)
        log_txt = f'/data/log/vest/releaseapk_{datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")}.txt'
        # print(f'{log_txt}')
        ini_file = os.path.join(constants.path_self, 'release.ini')
        ini_str = FilePlugin.read_str_from_file(ini_file)
        old_log_path = re.compile('log=[\\.\\w/-]+').search(ini_str).group().strip().lstrip()
        ini_str = ini_str.replace(old_log_path, f'log={log_txt}')
        FilePlugin.wirte_str_to_file(ini_str, ini_file)
        print('============================================')
        print(f'配置文件如下： ')
        print(f'{ini_str}')
        print('============================================')
        # 后台执行命令并输出日志
        print(f'执行 >>> nohup python release.py > {log_txt} 2>&1 &')
        print(f'查看日志输出 {log_txt}')
        print(os.system(f'nohup python release.py > {log_txt} 2>&1 &'))
        pass

    @staticmethod
    def yd_jiagu(file, jks, output):
        print(f'接收到的apk文件 >>> {file}')
        print(f'接收到的jks文件 >>> {jks}')
        print(f'接收到的输出路径 >>> {output}')
        print(f'开始加固apk....')
        out_file = Jiagu.jiagu(file, jks, output)
        if out_file is not None:
            Entry.sign_apk(out_file, jks, None)
        pass

    @staticmethod
    def sign_apk(file, jks, output):
        print(f'接收到的apk文件 >>> {file}')
        print(f'接收到的jks文件 >>> {jks}')
        print(f'接收到的输出路径 >>> {output}')
        print(f'开始签名apk....')
        return Sign.sign(file, jks, 'LS880617\!@#', output)
        pass

    @staticmethod
    def create_jkss():
        print(f'JKS配置文件如下：')
        print(f'{FilePlugin.read_str_from_file("./jks.ini")}')
        os.chdir('/root/sung/python/project/assembleVestApk')
        builder = JKSCreate('./jks.ini')
        builder.creat_multi_jks()
        pass

    @staticmethod
    def start_server_api():
        # python manage.py runserver 0.0.0.0:8000 --settings=settings.dev
        path = '/root/sung/python/django/netserver/'
        ini_path = os.path.join(path, 'run.ini')
        os.chdir(path)
        # 停止已有服务
        stop_command = "ps -ef |grep manage.py |grep -v grep |awk '{print $2}' |xargs kill -9"
        if os.system(stop_command) == 0:
            print('停止django进程成功！')
        # 读取启动配置
        config = configparser.ConfigParser()
        config.read(ini_path)
        run_ip = config.get('config', 'run_ip')
        env = config.get('config', 'env')
        log_txt = f'/data/log/server/log_{str(time.strftime("%Y%m%d%H%M%S"))}.txt'
        content = FilePlugin.read_str_from_file(ini_path)
        print(f'>>>>>>>>>>>')
        print(f'服务器配置如下：')
        print(f'{content}')
        print(f'>>>>>>>>>>>')
        # 后台启动
        command = f'(nohup python manage.py runserver {run_ip} --settings={env} > {log_txt} 2>&1 &)'
        print(f'命令行输出到日志：{log_txt}')
        # print(f'{command}')
        result = os.system(command)
        print('启动成功！' if result == 0 else '启动失败!')
        # 通知
        notice = Notice()
        notice.notice_wechat(WebHook.url_wechat_bot, Notice.build_rebot_content(
            result == 0, log_txt, int(run_ip.split(':')[1]), env.split('.')[1]))
        pass

    @staticmethod
    def stop_server_api():
        stop_command = "ps -ef |grep manage.py |grep -v grep |awk '{print $2}' |xargs kill -9"
        notice = Notice()
        base_ = '{"msgtype": "markdown","markdown":{"title":"服务器API停止通知","content":"contentstr"}}'
        if os.system(stop_command) == 0:
            print('停止django进程成功！')
            notice.notice_wechat(WebHook.url_wechat_bot, base_.replace('contentstr', '服务器API进程监听已被停止！'))
            return
        print('停止失败！')
        notice.notice_wechat(WebHook.url_wechat_bot, base_.replace('contentstr', '尝试停止服务器API进程监听失败！'))
        pass


if __name__ == '__main__':
    """
    工具集合入口，自定义选择执行脚本
    """
    print('----------------------------------------------')
    print('以下是可供选择的项：')
    print(f'【1】重置huajian-android内的本地properties文件'.join(("\033[7m", "\033[0m")))
    print(f'【2】回退huajian-android所有变更代码'.join(("\033[7m", "\033[0m")))
    print(f'【3】拉取huajian-android项目hjvest_user_safe分支最新代码'.join(("\033[7m", "\033[0m")))
    print(f'【4】执行huajian-android项目gradle.clean'.join(("\033[7m", "\033[0m")))
    print(f'【5】马甲包打包'.join(("\033[7m", "\033[0m")))
    print(f'【6】使用易盾加固apk'.join(("\033[7m", "\033[0m")))
    print(f'【7】apk签名'.join(("\033[7m", "\033[0m")))
    print(f'【8】批量创建jks文件（配置文件jks.ini）'.join(("\033[7m", "\033[0m")))
    print(f'【9】启动服务端api监听'.join(("\033[7m", "\033[0m")))
    print(f'【10】停止服务端api监听'.join(("\033[7m", "\033[0m")))
    print('>>>')
    print(f'不输入内容按Enter退出')
    try:
        print('----------------------------------------------')
        inp = int(input('请输入执行选项：'))
        if inp == 1:
            Entry.reset_properties()
        elif inp == 2:
            Entry.rollback()
        elif inp == 3:
            Entry.pull_origin_code('hjvest_user_safe')
        elif inp == 4:
            Entry.gradle_clean()
        elif inp == 5:
            Entry.release_apk()
        elif inp == 6 or inp == 7:
            # apk路径
            apk_file = str(input('请输入apk绝对路径：'))
            if apk_file is None or len(apk_file) == 0:
                print("路径不可为空！\n")
                sys.exit(0)
            else:
                if not apk_file.endswith('.apk'):
                    print('非法的apk文件！\n')
                    sys.exit(0)
                # jks路径
                jks_file = str(input('请输入jks签名文件绝对路径：'))
                if jks_file is None or len(jks_file) == 0:
                    print("路径不可为空！\n")
                    sys.exit(0)
                else:
                    if not jks_file.endswith('.jks'):
                        print('非法的jks文件！\n')
                        sys.exit(0)
                    # 输出路径
                    output_dir = str(input("请输入apk文件输出位置（默认源文件所在文件夹）"))
                    if output_dir is None or len(output_dir) == 0:
                        output_dir = '/data/backup/apks/'
                    if inp == 6:
                        # 执行加固
                        Entry.yd_jiagu(apk_file, jks_file, output_dir)
                    elif inp == 7:
                        # 执行签名
                        Entry.sign_apk(apk_file, jks_file, output_dir)
        elif inp == 8:
            Entry.create_jkss()
        elif inp == 9:
            Entry.start_server_api()
        elif inp == 10:
            Entry.stop_server_api()
        else:
            sys.exit(0)
    except Exception as e:
        sys.exit(0)
    pass
