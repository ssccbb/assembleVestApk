# coding=utf-8
import re
import sys

import constants
from files.plugin.FilePlugin import *


class Jiagu:

    def __init__(self):
        pass

    @staticmethod
    def jiagu(file: str, jks: str, output: str):
        print(f'待加固apk文件路径 >>> {file}')
        print(f'待加固jks文件路径 >>> {jks}')
        print(f'输出文件路径 >>> {output}')
        if file is None or len(file) == 0:
            print("请保证apk文件路径正确!")
            sys.exit(0)
        if jks is None or len(jks) == 0:
            print("请保证jks文件路径正确!")
            sys.exit(0)
        # 1.重置config.ini签名文件路径
        ini_file = os.path.join(constants.path_self, 'files/ydjiagu/config.ini')
        print(f'加固配置文件路径 >>> {ini_file}')
        config = FilePlugin.read_str_from_file(ini_file)
        if config.find('keystore=') == -1:
            print("配置文件出错！请检查配置文件签名 keystore 字段")
            sys.exit(99)
        old_jks_path = re.compile('keystore=[\\w+./_]+').search(config).group().strip().lstrip()
        print(f'jks === {old_jks_path}')
        FilePlugin.wirte_str_to_file(config.replace(old_jks_path, 'keystore=' + jks), ini_file)
        # 2.执行加固
        # java -jar $JAR_PATH -yunconfig -fullapk -apksign -input $arg1 -output $last_output
        paths = file.split('/')
        apk_name = paths[len(paths) - 1]
        apk_dir = file.replace(f'/{apk_name}', '')
        print(f'{apk_name}  {apk_dir}')
        if output is not None and len(output) > 0 and os.path.exists(output):
            last_output = (output[:len(output) - 1] if output.endswith(
                '/') else output) + f'/{apk_name.replace(".apk", "_protected.apk")}'
        else:
            last_output = apk_dir.replace(".apk", "_protected.apk")
        command = f'java -jar {os.path.join(constants.path_self, "files/jar/NHPProtect.jar")}' \
                  f' -yunconfig -fullapk -apksign -config {ini_file} -input {file} -output {last_output}'
        print(os.system(f'{command}'))
        if os.path.exists(last_output):
            print(f'加固任务执行完成！输出文件路径 >>> {last_output}')
            return last_output
        else:
            print('加固任务执行失败！')
        pass
