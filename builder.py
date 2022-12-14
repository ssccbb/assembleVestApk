# coding=utf-8
import configparser
import time, constants, sys
from pathlib import Path
from files.plugin.Notification import Notice, WebHook
from files.plugin.FilePlugin import FilePlugin
from files.plugin.PackagePlugin import PackageParser
from files.plugin.git import *
from virus.Process import Process
from files.ydjiagu.YDJiagu import *
from tools import Entry
from virus.encrypt.AES import AES


def deco(func):
    """
    装饰器打印方法耗时
    :param func: 执行的方法
    :return:
    """

    def wrapper(*args, **kwargs):
        start_time = time.time()
        print(("开始执行 >>> %s" % str(func)).join(("\033[7m", "\033[0m")))
        func(*args, **kwargs)
        end_time = time.time()
        msecs = (end_time - start_time) * 1000
        print(("执行方法%s耗时 >>> %d ms" % (str(func), msecs)).join(("\033[7m", "\033[0m")))

    return wrapper


class ReleaseBuilder:

    def __init__(self, regular: bool, base: bool, version: str, packages: dict, jiagu: bool, log: str):
        """
        构建流程
        渠道、版本、openinstall
        是默认不写进打包配置的所以在package.json内可不做修改
        """
        # 是否需要在打包时加入报毒混淆
        self.need_regular = regular
        # 是否是基准包
        self.need_base_apk = base
        # 统一版本号
        self.base_version_name = version
        # 需要生成的包名列表
        self.package_list = packages
        # 签名文件
        self.jks_path = ''
        # 是否需要加固
        self.yd_jiagu = jiagu
        # 日志文件地址
        self.log_txt = log
        pass

    def assemble_list_(self):
        """
        批量生成apk
        :return:
        """
        for package in self.package_list.keys():
            # 清空ini文件夹
            print(f'清空配置文件夹 >>>>')
            for sub in os.listdir(constants.path_ini):
                FilePlugin.remove_path_file(os.path.join(constants.path_ini, sub))
            # 开始单个打包
            print(f'当前打包任务，执行包名 >>>> {package}')
            back_path = os.path.join(constants.path_self, f'files/jks/{package}')
            if not os.path.exists(back_path):
                print(
                    f'包名配置备份文件不存在 >>>> {back_path}\n===========================\n包名{package}因配置无效被跳过！\n===========================\n')
                continue
            for path in os.listdir(back_path):
                real_path = os.path.join(back_path, path)
                tar_path = os.path.join(constants.path_ini, path)
                if os.path.isfile(real_path):
                    # 复制图标以及json文件
                    FilePlugin.copy_file(real_path, tar_path)
                elif os.path.isdir(real_path):
                    if not os.path.exists(tar_path):
                        # 创建 ini/*** 包名文件夹
                        FilePlugin.mkdir(tar_path)
                    for file in os.listdir(real_path):
                        if os.path.isfile(os.path.join(real_path, file)):
                            # 复制jks
                            FilePlugin.copy_file(os.path.join(real_path, file), os.path.join(tar_path, file))
            jks_ = os.path.join(constants.path_ini, package + "/yr_release_key.jks")
            icon_ = os.path.join(constants.path_ini, "app_icon.png")
            json_ = os.path.join(constants.path_ini, "package.json")
            channel_ = os.path.join(constants.path_ini, 'channel.ini')
            if not os.path.exists(icon_):
                FilePlugin.copy_file(os.path.join(constants.path_self, 'res/app_icon.png'), icon_)
            if not os.path.exists(jks_):
                print(
                    f'jks文件不存在 >>>> {jks_}\n===========================\n包名{package}因配置无效被跳过！\n===========================\n')
                continue
            if not os.path.exists(json_):
                print(
                    f'包配置文件不存在 >>>> {json_}\n===========================\n包名{package}因配置无效被跳过！\n===========================\n')
                continue
            if not os.path.exists(channel_):
                print(f'channel.ini配置文件不存在 >>>> 包名{package}未配置离线推送渠道')
            # 先回退不必要的动
            git = Git(constants.path_android)
            git.remove_local_change()
            # 基准包配置
            self.do_base_change()
            # 打包执行
            self.assemble_single_()
        pass

    def assemble_single_(self):
        """
        单个生成apk
        :return:
        """
        # 每次编译前检查一下local.properties(NDK检查)
        self.check_local_properties()
        ini_package_name = PackageHelper.query_package_name()
        json_parser = PackageParser(ini_package_name, constants.path_ini + "/package.json")

        package_name = json_parser.read_value_with_key("packageName")
        app_name = json_parser.read_value_with_key("appName")
        version_name = json_parser.read_value_with_key("versionName")
        version_code = json_parser.read_value_with_key("versionCode")
        channel = json_parser.read_value_with_key("channel")

        yd_key = json_parser.read_value_with_key("ydKey")
        qq_ini = json_parser.read_value_with_key("qqKey")
        qq_appid = qq_ini[0]
        qq_appkey = qq_ini[1]
        wechat_ini = json_parser.read_value_with_key("wechatKey")
        wechat_appid = wechat_ini[0]
        wechat_appkey = wechat_ini[1]
        op_key = json_parser.read_value_with_key("openinstallKey")

        hide_slogan = json_parser.read_value_with_key("hideSlogan")
        hide_one_yuan = json_parser.read_value_with_key("hideOneYuan")
        hide_qq_login = json_parser.read_value_with_key("hideQQLogin")
        hide_wx_login = json_parser.read_value_with_key("hideWXLogin")
        hide_setting = json_parser.read_value_with_key("hideSetting")
        hide_guide = json_parser.read_value_with_key("hideGuide")
        hide_teen = json_parser.read_value_with_key("hideTeen")
        hide_permission_dialog = json_parser.read_value_with_key("hidePermissionDialog")
        hide_dialog = json_parser.read_value_with_key("hideDialog")

        print("开始打包前请核对以下相关包信息:")
        print(" ------- 包名：" + package_name)
        print(" ------- 应用名：" + app_name)
        print(" ------- 对外版本号：" + version_name)
        print(" ------- 对内版本号：" + version_code)
        print(" ------- 渠道：" + channel)
        print(" ------- 易盾一键登录：" + yd_key)
        print(" ------- QQ appid：" + qq_appid)
        print(" ------- QQ key：" + qq_appkey)
        print(" ------- 微信 appid：" + wechat_appid)
        print(" ------- 微信 key：" + wechat_appkey)
        print(" ------- OP：" + op_key)
        print(" ------- 隐藏包名相关UI：" + str(hide_slogan))
        print(" ------- 隐藏一元充值弹窗：" + str(hide_one_yuan))
        print(" ------- 隐藏QQ登录：" + str(hide_qq_login))
        print(" ------- 隐藏微信登录：" + str(hide_wx_login))
        print(" ------- 隐藏部分设置：" + str(hide_setting))
        print(" ------- 隐藏引导页：" + str(hide_guide))
        print(" ------- 隐藏青少年相关：" + str(hide_teen))
        print(" ------- 隐藏权限弹窗说明：" + str(hide_permission_dialog))
        print(" ------- 隐藏部分充值弹窗：" + str(hide_dialog))

        root_path = constants.path_android
        package_helper = PackageHelper(root_path)
        if not package_helper.check_file_change_status(ini_package_name):
            # step 1 ：替换应用名
            package_helper.change_app_name(app_name)
            # step 2 ：替换应用图标
            package_helper.change_app_icon(constants.path_ini + "/" + constants.old_app_icon)
            # step 3 ：替换应用签名文件
            self.jks_path = constants.path_ini + "/" + package_name + "/" + constants.old_app_jks
            package_helper.change_app_jks(self.jks_path)
            # step 4 ：更改应用包名以及wxapi回调路径包名
            package_helper.change_app_package(package_name)
            # step 5 ：更改其他配置相关
            package_helper.change_app_ini(self.need_base_apk, json_parser)
            package_helper.change_app_push(os.path.join(constants.path_ini, 'channel.ini'))
        # step 6 : 修改图片以及文本文件md5 （do_virus_change()方法内处理）
        # package_helper.change_md5()
        # step 7 : 修改代码文件(除wxapi)所在包名路径
        package_helper.change_random_package()
        # step 8 : 加入报毒处理方案
        self.do_virus_change()
        # step 9 : gradle
        print("开始执行gradle打包...")
        os.chdir(package_helper.path_android)
        # os.system("gradle aDR --offline")
        # 因为引入了stringfog在打包前需要clean一下防止解码缓存导致的解码失败
        os.system("gradle clean")
        os.system("gradle --no-daemon assembleRelease")
        # # step 10 : 拷贝文件
        apk_dir = os.path.join(package_helper.path_android, "app/build/outputs/apk/standard/release")
        if not os.path.exists(apk_dir):
            package_helper.notice_bot_error(package_name)
            print("ERROR! >>> 找不到apk文件")
            sys.exit(99)
        # 开始处理生成的apk
        for sub_file in os.listdir(apk_dir):
            if sub_file.endswith(".apk"):
                apk_file = os.path.join(apk_dir, sub_file)
                # 拷贝至外网apk
                public_apk = os.path.join(constants.path_zhouqipa_cn_files, sub_file)
                FilePlugin.copy_file(apk_file, public_apk)
                # 加固签名
                yd_sign_file = None
                if self.yd_jiagu and not self.need_base_apk:  # 基准包不需要加固
                    yd_sign_file = package_helper.yd_jiagu(public_apk, self.jks_path, constants.path_zhouqipa_cn_files)
                # bot通知
                jiagu_status = False
                if yd_sign_file is not None:
                    yd_paths = yd_sign_file.split('/')
                    sub_file = yd_paths[len(yd_paths) - 1]  # 存在加固apk的话使用加固apk通知
                    jiagu_status = True
                package_helper.notice_bot(self.need_base_apk,  # 是否基准包
                                          sub_file,  # 文件名
                                          package_name,  # 包名
                                          app_name,  # 应用名
                                          self.base_version_name,  # 版本号
                                          jiagu_status,  # 加固状态
                                          True,  # 签名状态（默认打包带签名配置，加固也必定会签名）
                                          self.log_txt,  # 日志文件地址
                                          self.package_list.get(package_name)  # ini内的备注信息
                                          )
                # 项目内apk
                tar_dir = os.path.join(constants.path_self, "outputs")
                FilePlugin.move_file(apk_file, tar_dir)
                print("apk文件已经转移至文件夹 >>> " + tar_dir)
        # 开始回退代码
        package_helper.code_rollback()
        # git在回退代码时会把本地文件移除（此操作仅仅是为了下次gradle执行方便,不做也可以）
        self.check_local_properties()
        print("DONE!")
        # sys.exit(0)
        pass

    def check_local_properties(self):
        local_properties = os.path.join(constants.path_android, "local.properties")
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

    def do_base_change(self):
        """
        根据需要是否需要做马甲包配置修改
        :return:
        """
        json_ = os.path.join(constants.path_ini, "package.json")
        ini_ = FilePlugin.read_str_from_file(json_)
        # "versionName": "14.9.00"
        old_version_name = re.compile('"versionName":\\s+".*"').search(ini_).group().strip().split(':')[1].replace('"',
                                                                                                                   '').lstrip().strip()
        # 为空的话默认代码版本号
        ini_ = ini_.replace(old_version_name, self.base_version_name)
        if not self.need_base_apk:
            FilePlugin.wirte_str_to_file(ini_, json_)
            return
        # "appName": "基准包应用名",
        old_app_name = re.compile('"appName":\\s+".*"').search(ini_).group().strip().split(':')[1].replace('"',
                                                                                                           '').lstrip().strip()
        new_app_name = '基准包应用名'
        if old_app_name != new_app_name:
            ini_ = ini_.replace(old_app_name, new_app_name)
        # "hideSlogan": false,
        old_hide_slogan = re.compile('"hideSlogan":\\s+(true|false)').search(ini_).group().strip().split(':')[
            1].lstrip().strip()
        if old_hide_slogan != 'true':
            ini_ = ini_.replace(f'"hideSlogan": {old_hide_slogan}', f'"hideSlogan": true')
        # "hideSetting": false,
        old_hide_setting = re.compile('"hideSetting":\\s+(true|false)').search(ini_).group().strip().split(':')[
            1].lstrip().strip()
        if old_hide_setting != 'true':
            ini_ = ini_.replace(f'"hideSetting": {old_hide_setting}', f'"hideSetting": true')
        # "hideGuide": false,
        old_hide_guide = re.compile('"hideGuide":\\s+(true|false)').search(ini_).group().strip().split(':')[
            1].lstrip().strip()
        if old_hide_guide != 'true':
            ini_ = ini_.replace(f'"hideGuide": {old_hide_guide}', f'"hideGuide": true')
        # "hideTeen": false,
        old_hide_teen = re.compile('"hideTeen":\\s+(true|false)').search(ini_).group().strip().split(':')[
            1].lstrip().strip()
        if old_hide_teen != 'true':
            ini_ = ini_.replace(f'"hideTeen": {old_hide_teen}', f'"hideTeen": true')
        FilePlugin.wirte_str_to_file(ini_, json_)
        pass

    def do_virus_change(self):
        """
        根据需要是否需要做报毒相关处理
        :return:
        """
        if not self.need_regular:
            return
        process = Process(constants.path_android)
        # 移除无用string
        process.remove_unuse_strings_in_xml()
        # 垃圾代码
        process.build_junk_code_with_gradle()
        # 重写用到的加密后字符串
        process.rewrite_encrypt_string()
        # 重写stringfog密钥
        process.rewrite_string_fog()
        # 更改可编辑文件md5
        process.change_file_md5()
        pass


class PackageHelper:
    """
    构建工具类
    """

    def __init__(self, path: str):
        print("inti package helper")
        # 安卓项目根路径
        self.path_android = path
        # 安卓项目代码路径
        self.path_android_code = self.path_android + "/app/src/main/java"
        # 安卓项目res路径
        self.path_android_res = self.path_android + "/app/src/main/res"
        # 安卓项目包路径
        self.path_android_package = self.path_android + "/app/src/main/java/com/yr/jksdemo"
        # gradle.properties配置参数文件路径
        self.path_android_properties = self.path_android + "/gradle.properties"
        # 字符串文件路径
        self.path_android_string = self.path_android_res + "/values/strings.xml"
        # file_paths
        self.path_android_filepath = self.path_android_res + "/xml/file_paths.xml"

    @deco
    def check_file_change_status(self, package_name):
        dirs = package_name.split(".")
        path = self.path_android_code
        for subdir in dirs:
            if len(subdir.strip()) != 0:
                path = os.path.join(path, subdir)
        print("check >>> " + path)
        path = os.path.join(path, "wxapi")
        if os.path.exists(path) and os.listdir(path) and os.path.exists(
                os.path.join(path, "WXEntryActivity.java")) and os.path.exists(
            os.path.join(path, "WXPayEntryActivity.java")):
            print("检测到文件已做修改,即将跳过文件修改步奏...")
            return True
        print("执行文件修改步奏...")
        return False
        pass

    @staticmethod
    def query_package_name():
        """
        查询配置文件夹的包名
        :return: packagename
        """
        for sub_dir in os.listdir(constants.path_ini):
            sub_file = Path(constants.path_ini + "/" + sub_dir)
            if sub_file.is_dir():
                print("于 " + constants.path_ini + " 路径内查询到可用包名 ：" + sub_dir)
                return sub_dir
        return ""

    def change_app_name(self, app_name):
        """
        修改应用名
        :param app_name:
        :return:
        """
        print("开始替换appname ------ " + app_name)
        # path_android_string
        FilePlugin.change_str_in_file("vestname", app_name, self.path_android_string)
        FilePlugin.change_str_in_file("vestname", app_name, self.path_android_properties)
        pass

    def change_app_icon(self, path_file):
        """
        修改应用图标
        :param path_file:
        :return:
        """
        print("开始替换appicon ------ " + path_file)
        old_app_icon = self.path_android_res + "/mipmap-xxhdpi/" + constants.old_app_icon
        print("md5 >>> " + FilePlugin.md5(old_app_icon))
        FilePlugin.replace_file(old_app_icon, path_file)
        print("md5(new) >>> " + FilePlugin.md5(old_app_icon))
        print("执行完成")
        pass

    def change_app_jks(self, path_file):
        """
        修改签名文件
        :param path_file:
        :return:
        """
        print("开始替换签名文件 ------ " + path_file)
        old_app_jks = self.path_android + "/" + constants.old_app_jks
        print("md5 >>> " + FilePlugin.md5(old_app_jks))
        FilePlugin.replace_file(old_app_jks, path_file)
        print("md5(new) >>> " + FilePlugin.md5(old_app_jks))
        print("执行完成")
        pass

    @deco
    def change_app_package(self, app_package_name):
        """
        修改应用包名
        :param app_package_name:
        :return:
        """
        print("开始修改包名路径 ------ " + app_package_name)
        # properties
        self.replace_content("APP_PACKAGENAME=", app_package_name.strip(), self.path_android_properties)
        # wxapi回调包名
        app_package_name_list = app_package_name.split(".")
        new_path = self.path_android_code
        for dirname in app_package_name_list:
            new_path = new_path + "/" + dirname
        FilePlugin.rename_path(self.path_android_package, new_path)
        # com/syzdmsc/hjbm
        for root, dirs, files in os.walk(new_path):
            for subdir in dirs:
                # com/syzdmsc/hjbm/wxapi
                wxapi_dir = os.path.join(root, subdir)
                for wxapi_root, wxapi_dirs, wxapi_files in os.walk(wxapi_dir):
                    # WXEntryActivity.java
                    # WXPayEntryActivity.java
                    for wxapi_file in wxapi_files:
                        filename = os.path.join(wxapi_dir, wxapi_file)
                        if filename.endswith(".java"):
                            print("开始执行包名头部路径替换...." + filename)
                            with open(filename, mode='r') as f:
                                data = f.read()
                                f.close()
                            with open(filename, mode='w') as f:
                                content = data.replace(constants.old_app_wxapi_path, app_package_name)
                                f.write(content)
                                f.close()
        # file_path.xml
        FilePlugin.change_str_in_file(constants.old_app_package, app_package_name, self.path_android_filepath)
        pass

    @deco
    def change_random_package(self):
        """
        修改除wxapi回调代码以外的代码文件所在的包路径
        :return:
        """
        pass

    def change_app_ini(self, is_base_apk: bool, ini_dict):
        """
        修改其他配置参数
        :param is_base_apk: 是否是基准（影响h5跳转方式）
        :param ini_dict:
        :return:
        """
        print("开始修改其他配置参数 ------ " + str(ini_dict))
        aes = AES(self.path_android)
        properties_file = self.path_android_properties
        self.replace_content("APP_PACKAGENAME=", ini_dict.read_value_with_key("packageName").strip(),
                             properties_file)
        version_name = ini_dict.read_value_with_key("versionName").strip()
        if len(version_name) > 0:
            self.replace_content("APP_VERSION=", ini_dict.read_value_with_key("versionName").strip(),
                                 properties_file)
        # full_channel = ini_dict.read_value_with_key("channel")
        # self.replace_content("MAIN_CHANNEL=", full_channel.split("_")[0], properties_file)
        # self.replace_content("SUB_CHANNEL=", full_channel.split("_")[1], properties_file)
        self.replace_content("YD_APPID=", ini_dict.read_value_with_key("ydKey"), properties_file)

        self.replace_content("CHROME_PAY=", 'true' if is_base_apk else 'false', properties_file)
        # self.replace_content("CHROME_PAY=", 'true', properties_file)
        #self.replace_content("CHROME_PAY=", 'false', properties_file)

        qq_ini = ini_dict.read_value_with_key("qqKey")
        self.replace_content("QQ_APPID=", qq_ini[0].strip(), properties_file)
        self.replace_content("QQ_KEY=", qq_ini[1].strip(), properties_file)
        wechat_ini = ini_dict.read_value_with_key("wechatKey")
        self.replace_content("WECHAT_APPID=", wechat_ini[0].strip(), properties_file)
        self.replace_content("WECHAT_KEY=", wechat_ini[1].strip(), properties_file)
        # self.replace_content("KEY_OPENINSTALL=", ini_dict.read_value_with_key("openinstallKey"),
        #                      properties_file)
        get_appid = ini_dict.read_value_with_key("gtappid")
        if len(get_appid) > 0:
            self.replace_content("GT_APPID=", aes.encrypt_string_with_key(get_appid, aes.old_aes_key), properties_file)
        jpush = ini_dict.read_value_with_key("jpush")
        if jpush is not None and len(jpush) > 0:
            self.replace_content("JPUSH_ID=", aes.encrypt_string_with_key(jpush[0].strip(), aes.old_aes_key), properties_file)
            self.replace_content("JPUSH_CHANNEL=", aes.encrypt_string_with_key(jpush[1].strip(), aes.old_aes_key), properties_file)
        self.replace_content("HIDE_SLOGAN=", str(ini_dict.read_value_with_key("hideSlogan")).lower(),
                             properties_file)
        self.replace_content("HIDE_ONEYUANDIALOG=", str(ini_dict.read_value_with_key("hideOneYuan")).lower(),
                             properties_file)
        self.replace_content("HIDE_QQLOGIN=", str(ini_dict.read_value_with_key("hideQQLogin")).lower(),
                             properties_file)
        self.replace_content("HIDE_WXLOGIN=", str(ini_dict.read_value_with_key("hideWXLogin")).lower(),
                             properties_file)
        self.replace_content("HIDE_SETTING=", str(ini_dict.read_value_with_key("hideSetting")).lower(),
                             properties_file)
        self.replace_content("HIDE_GUIDE=", str(ini_dict.read_value_with_key("hideGuide")).lower(),
                             properties_file)
        self.replace_content("HIDE_TEEN=", str(ini_dict.read_value_with_key("hideTeen")).lower(),
                             properties_file)
        self.replace_content("HIDE_PERMISSIONDIALOG=",
                             str(ini_dict.read_value_with_key("hidePermissionDialog")).lower(),
                             properties_file)
        self.replace_content("HIDE_DIALOG=", str(ini_dict.read_value_with_key("hideDialog")).lower(),
                             properties_file)
        # 服务器只有4g 低了卡gradle高了容易崩溃
        self.replace_content("org.gradle.jvmargs=", "-Xmx1024m", properties_file)
        # 守护进程关闭
        FilePlugin.change_str_in_file("#org.gradle.daemon=false", "org.gradle.daemon=false", properties_file)
        # 单gradle多任务并行构建关闭
        FilePlugin.change_str_in_file("#org.gradle.parallel=false", "org.gradle.parallel=false", properties_file)
        FilePlugin.change_str_in_file("./" + constants.old_app_jks,
                                      os.path.join(self.path_android, constants.old_app_jks),
                                      os.path.join(self.path_android, "app/build.gradle"))
        print(str(properties_file) + " 配置替换完成！")
        pass

    def change_app_push(self, channel_ini: str):
        print(f'开始修改离线推送配置参数 ------------')
        if not os.path.exists(channel_ini):
            print(f'{channel_ini} 文件不存在！')
            return
        aes = AES(self.path_android)
        config = configparser.ConfigParser()
        config.read(filenames=channel_ini)
        result_head = f'public static final String '
        result_middle = f' = VestHelper.getInstance().decodeAESString'
        print(f'=============channel.ini===============')
        print(f'{FilePlugin.read_str_from_file(channel_ini)}')
        print(f'=============channel.ini===============')
        # 华为
        hw_appid = str(config.get('hw', 'appid'))
        # hw_appkey = str(config.get('hw', 'appkey'))
        # hw_secret = str(config.get('hw', 'secret'))
        hw_certificatename = str(config.get('hw', 'certificatename'))
        if hw_appid is not 'appid':
            self.replace_content(f'{result_head}hwAppId{result_middle}',
                                 f'("{aes.encrypt_string_with_key(hw_appid, aes.old_aes_key)}");', aes.path_target_file)
        if hw_certificatename is not 'certificatename':
            self.replace_content(f'{result_head}hwCertificateName{result_middle}',
                                 f'("{aes.encrypt_string_with_key(hw_certificatename, aes.old_aes_key)}");', aes.path_target_file)
        # 魅族
        mz_appid = str(config.get('mz', 'appid'))
        mz_appkey = str(config.get('mz', 'appkey'))
        # mz_secret = str(config.get('mz', 'secret'))
        mz_certificatename = str(config.get('mz', 'certificatename'))
        if mz_appid is not 'appid':
            self.replace_content(f'{result_head}mzAppId{result_middle}',
                                 f'("{aes.encrypt_string_with_key(mz_appid, aes.old_aes_key)}");', aes.path_target_file)
        if mz_appkey is not 'appkey':
            self.replace_content(f'{result_head}mzAppKey{result_middle}',
                                 f'("{aes.encrypt_string_with_key(mz_appkey, aes.old_aes_key)}");', aes.path_target_file)
        if mz_certificatename is not 'certificatename':
            self.replace_content(f'{result_head}mzCertificateName{result_middle}',
                                 f'("{aes.encrypt_string_with_key(mz_certificatename, aes.old_aes_key)}");', aes.path_target_file)
        # OPPO
        oppo_appid = str(config.get('oppo', 'appid'))
        oppo_appkey = str(config.get('oppo', 'appkey'))
        oppo_secret = str(config.get('oppo', 'secret'))
        oppo_certificatename = str(config.get('oppo', 'certificatename'))
        if oppo_appid is not 'appid':
            self.replace_content(f'{result_head}oppoAppId{result_middle}',
                                 f'("{aes.encrypt_string_with_key(oppo_appid, aes.old_aes_key)}");', aes.path_target_file)
        if oppo_appkey is not 'appkey':
            self.replace_content(f'{result_head}oppoAppKey{result_middle}',
                                 f'("{aes.encrypt_string_with_key(oppo_appkey, aes.old_aes_key)}");', aes.path_target_file)
        if oppo_secret is not 'secret':
            self.replace_content(f'{result_head}oppoAppSercet{result_middle}',
                                 f'("{aes.encrypt_string_with_key(oppo_secret, aes.old_aes_key)}");', aes.path_target_file)
        if oppo_certificatename is not 'certificatename':
            self.replace_content(f'{result_head}oppoCertificateName{result_middle}',
                                 f'("{aes.encrypt_string_with_key(oppo_certificatename, aes.old_aes_key)}");', aes.path_target_file)
        print(f'更换VestHelper.java内离线推送配置执行完成！')
        pass

    def replace_content(self, tag, content, target_file):
        if len(tag) == 0 or len(content) == 0:
            return
        with open(target_file, mode='r') as f:
            read_lines = f.readlines()
            f.close()
        with open(target_file, mode='w') as f:
            for line in read_lines:
                line = line.lstrip()
                if line.startswith(tag):
                    line_new = line.replace(line, tag + content)
                    if line.endswith("\n"):
                        line_new = line_new + "\n"
                    f.writelines(line_new)
                else:
                    f.writelines(line)
            f.close()
        pass

    @deco
    def change_md5(self):
        """
        重置项目内可编辑文件md5值
        :return:
        """
        # FilePlugin.reset_files_md5(self.path_android)
        FilePlugin.reset_files_md5(os.path.join(self.path_android, "app"))
        FilePlugin.reset_files_md5(os.path.join(self.path_android, "library-beauty"))
        FilePlugin.reset_files_md5(os.path.join(self.path_android, "library-commonlib"))
        FilePlugin.reset_files_md5(os.path.join(self.path_android, "library-eventbus"))
        FilePlugin.reset_files_md5(os.path.join(self.path_android, "library-im"))
        FilePlugin.reset_files_md5(os.path.join(self.path_android, "module-community"))
        FilePlugin.reset_files_md5(os.path.join(self.path_android, "module-ext"))
        FilePlugin.reset_files_md5(os.path.join(self.path_android, "module-live"))
        FilePlugin.reset_files_md5(os.path.join(self.path_android, "module-message"))
        FilePlugin.reset_files_md5(os.path.join(self.path_android, "module-party"))
        FilePlugin.reset_files_md5(os.path.join(self.path_android, "module-vchat"))
        FilePlugin.reset_files_md5(os.path.join(self.path_android, "YR-Network"))
        FilePlugin.reset_files_md5(os.path.join(self.path_android, "YR-Player"))
        FilePlugin.reset_files_md5(os.path.join(self.path_android, "YR-SvgaImage"))
        FilePlugin.reset_files_md5(os.path.join(self.path_android, "YR-Tools"))
        FilePlugin.reset_files_md5(os.path.join(self.path_android, "YR-Uikit"))
        FilePlugin.reset_files_md5(os.path.join(self.path_android, "commonlibrary"))
        pass

    def code_rollback(self):
        """
        每次重新打包时做代码回退
        :return:
        """
        print("回退源代码执行中")
        git = Git(self.path_android)
        git.remove_local_change()
        pass

    def yd_jiagu(self, file, jks, output):
        print(f'接收到的apk文件 >>> {file}')
        print(f'接收到的jks文件 >>> {jks}')
        print(f'接收到的输出路径 >>> {output}')
        print(f'开始加固apk....')
        out_file = Jiagu.jiagu(file, jks, output)
        if out_file is not None:
            return Entry.sign_apk(out_file, jks, None)
        pass

    @staticmethod
    def notice_bot(base_apk: bool, file: str, package: str, app_name: str,
                   version: str, jiagu: bool, sign: bool, log: str, others: str):
        try:
            notice = Notice()
            if version is None or len(version) == 0:
                if file.count("_") > 0:
                    version = file.split("_")[1] if file.split("_")[1].startswith("v") else ""
            notice.notice_wechat(WebHook.url_wechat_bot,
                                 Notice.build_content(True, base_apk, file, package, app_name, version, jiagu, sign, log, others))
            notice.notice_ding_talk(WebHook.url_ding_talk_bot,
                                    Notice.build_content(False, base_apk, file, package, app_name, version, jiagu, sign, log, others))
        finally:
            print('通知发送完成')
        pass

    @staticmethod
    def notice_bot_error(package_name: str):
        try:
            notice = Notice()
            content = '{"msgtype": "markdown","markdown":{"content":"> buildtime 马甲包构建脚本执行失败！\n> 当前包名 >>> packagename"}}'
            content = content.replace('packagename', package_name)
            content = content.replace('buildtime', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            config = configparser.ConfigParser()
            config.read(filenames='./release.ini')
            log_txt = str(config.get('log', 'log'))
            if log_txt is not None and len(log_txt) > 0 and 'data' in log_txt:
                content = f'{content}\n>\n> [源log文件下载](http:zhouqipa.cn{log_txt.replace("data", "files")})'
            else:
                content = f'{content}\n> {log_txt}'
            notice.notice_wechat(WebHook.url_wechat_bot, content)
        finally:
            print('通知发送完成')
        pass
