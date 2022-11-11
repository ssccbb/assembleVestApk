# coding=utf-8
import os, constants, sys
from files.plugin.FilePlugin import *
from files.plugin.APKPlugin import *


class Sign:

    def __init__(self):
        print('签名工具初始化...')
        pass

    @staticmethod
    def sign(apk_file: str, jks_file: str, jks_password: str, output_dir: str):
        if apk_file is None or len(apk_file) == 0:
            print("请保证apk文件路径正确!")
            sys.exit(0)
        if jks_file is None or len(jks_file) == 0:
            print("请保证jks文件路径正确!")
            sys.exit(0)
        if jks_password is None or len(jks_password) == 0:
            print("请输入正确的JKS密码!")
            sys.exit(0)
        paths = apk_file.split('/')
        apk_name = paths[len(paths) - 1]
        apk_dir = apk_file.replace(f'/{apk_name}', '')
        print(f'源文件所在文件夹 >>> {apk_dir}')
        os.chdir(apk_dir)
        sign_content = f'-alias yr -pswd {jks_password} -aliaspswd {jks_password}'
        print(f'查询到需要签名的APK >>> {apk_name}')
        signed_apk = APKPlugin.signer_apk_file(jks_file, sign_content, apk_file)
        # remove未签名文件
        FilePlugin.remove_path_file(apk_file)
        if output_dir is None or len(output_dir) == 0:
            print(f'DONE！已签名文件 >>> {"" if signed_apk is None or len(signed_apk) == 0 else signed_apk}')
            return signed_apk
        else:
            if not os.path.exists(output_dir):
                print(f'Done! 指定输出路径不存在 >>> {output_dir} ,请前往源文件路径查找已签名apk')
                return signed_apk
            if signed_apk is None or len(signed_apk) == 0:
                print('Done!')
                return signed_apk
            signed_apk_paths = signed_apk.split('/')
            output_apk_file = os.path.join(
                output_dir if not output_dir.endswith('/') else output_dir[:len(output_dir) - 1],
                signed_apk_paths[len(signed_apk_paths) - 1])
            # print(f'{output_apk_file}')
            FilePlugin.move_file(signed_apk, output_apk_file)
            if os.path.exists(output_apk_file):
                # 存在软连接的情况 如果传入的文件夹与输出文件夹为绑定关系
                # 删掉源文件=删掉目标文件 move过后暂时不做remove处理
                # 手动处理文件过多的情况
                # FilePlugin.remove_path_file(signed_apk)
                print(f'Done！已签名文件 >>> {output_apk_file}')
                return output_apk_file
            print('Done!')
            return None
        pass
