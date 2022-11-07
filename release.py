# coding=utf-8
import os, re, constants
from builder import PackageHelper
from files.plugin.FilePlugin import FilePlugin
from files.plugin.PackagePlugin import PackageParser
from git import *
from virus.Process import Process

"""
渠道、版本、openinstall 
是默认不写进打包配置的所以在package.json内可不做修改
"""
# 是否需要在打包时加入报毒混淆
need_regular = True
# 是否是基准包
need_base_apk = False
# 统一版本号
base_version_name = "15.0.00"
# 需要生成的包名列表
package_list = ['com.bqhflu.vgjyat']


def assemble_list_():
    """
    批量生成apk
    :return:
    """
    for package in package_list:
        # 清空ini文件夹
        print(f'清空配置文件夹 >>>>')
        for sub in os.listdir(constants.path_ini):
            FilePlugin.remove_path_file(os.path.join(constants.path_ini, sub))
        # 开始单个打包
        print(f'开始单个打包=====包名{package}=====第{package_list.index(package) + 1}个包')
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
        # 先回退不必要的动
        git = Git(constants.path_android)
        git.remove_local_change()
        # 基准包配置
        do_base_change()
        # 打包执行
        assemble_single_()
    pass


def assemble_single_():
    """
    单个生成apk
    :return:
    """
    # 每次编译前检查一下local.properties(NDK检查)
    check_local_properties()
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
        package_helper.change_app_jks(constants.path_ini + "/" + package_name + "/" + constants.old_app_jks)
        # step 4 ：更改应用包名以及wxapi回调路径包名
        package_helper.change_app_package(package_name)
        # step 5 ：更改其他配置相关
        package_helper.change_app_ini(json_parser)
    # step 6 : 修改图片以及文本文件md5 （do_virus_change()方法内处理）
    # package_helper.change_md5()
    # step 7 : 修改代码文件(除wxapi)所在包名路径
    package_helper.change_random_package()
    # step 8 : 加入报毒处理方案
    do_virus_change()
    # step 9 : gradle
    print("开始执行gradle打包...")
    os.chdir(package_helper.path_android)
    # os.system("gradle aDR --offline")
    # 因为引入了stringfog在打包前需要clean一下防止解码缓存导致的解码失败
    os.system("gradle clean")
    os.system("gradle --no-daemon assembleRelease")
    # # step 10 : 拷贝文件
    apk_dir = os.path.join(package_helper.path_android, "app/build/outputs/apk/standard/release")
    for sub_file in os.listdir(apk_dir):
        if sub_file.endswith(".apk"):
            tar_dir = os.path.join(constants.path_self, "outputs")
            FilePlugin.move_file(os.path.join(apk_dir, sub_file), tar_dir)
            print("apk文件已经转移至文件夹 >>> " + tar_dir)
    package_helper.code_rollback()
    # git在回退代码时会把本地文件移除
    check_local_properties()
    print("done!")
    pass


def check_local_properties():
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


def do_base_change():
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
    ini_ = ini_.replace(old_version_name, base_version_name)
    if not need_base_apk:
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


def do_virus_change():
    """
    根据需要是否需要做报毒相关处理
    :return:
    """
    if not need_regular:
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


if __name__ == '__main__':
    assemble_list_()
    pass
