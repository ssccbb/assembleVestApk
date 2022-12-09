import configparser
import os, time, pexpect
import random
import sys


class JKSCreate:

    def __init__(self, *args):
        if len(args) == 1:
            # self, ini_path: str
            print('开始进行创建JKS前的配置确认....')
            config = configparser.ConfigParser()
            config.read(args[0])

            self.nums = config.getint('base', 'num')
            self.need_txt = config.getboolean('base', 'txt_info')
            self.need_r_package = config.getboolean('base', 'random_package')
            output = str(config.get('base', 'output'))
            if not os.path.exists(output):
                os.makedirs(output)
                print(f'当前路径 >>> {output} 不存在！已创建成功')
            self.real_output = os.path.join(output, f'jks_{str(time.strftime("%Y%m%d%H%M%S"))}')
            print(f'当前输出路径 >>> {self.real_output}')

            self.keystore = str(config.get('jks', 'keystore'))
            self.alias = str(config.get('jks', 'alias'))
            self.key_pass = str(config.get('jks', 'keypass'))
            self.key_size = config.getint('jks', 'keysize')
            self.validity = config.getint('jks', 'validity')
        elif len(args) == 3:
            # keystore: str, key_pass: str, output: str
            if not os.path.exists(args[2]):
                os.makedirs(args[2])
                print(f'当前路径 >>> {args[2]} 不存在！已创建成功')
            self.real_output = os.path.join(args[2], f'jks_{str(time.strftime("%Y%m%d%H%M%S"))}')
            print(f'当前输出路径 >>> {self.real_output}')
            os.makedirs(self.real_output)
            self.keystore = args[0]
            self.key_pass = args[1]
        pass

    def creat_multi_jks(self):
        """
        依据配置文件生成JKS
        :return:
        """
        if self.nums is None:
            print(f'错误的初始化方式！请检查方法调用！')
            sys.exit(0)
        print('开始批量生成JKS...')
        if self.nums <= 0:
            print(f'配置数量为0，即将退出...')
            sys.exit(0)
        if self.need_r_package:
            package_list = JKSCreate.random_package_list(self.nums)
        else:
            package_list = set()
            for i in range(self.nums + 1):
                package_list.add(f'jks{i}')
        for package in package_list:
            print(f'当前包名 {package}')
            jks_path = self.creat_single_jks(package, self.alias, self.key_pass, self.key_pass, 'RSA', self.key_size,
                                             self.validity)
            if self.need_txt:
                self.create_txt_info(jks_path, 'jks_info.txt', self.key_pass)
            print(f'包名JKS {package} 创建完成')
        pass

    def creat_single_jks(self, package: str, alias: str, store_pass: str, key_pass: str, key_alg: str, key_size: int,
                         validity: int):
        """
        创建单个jks文件
        :param package: 包名
        :param alias: 别名
        :param store_pass: 别名密码
        :param key_pass: 签名密码
        :param key_alg: RSA
        :param key_size: 长度
        :param validity: 有效期
        :return:
        """
        if self.real_output is None or len(self.real_output) == 0:
            print(f'错误的初始化方式！请检查方法调用！')
            sys.exit(0)
        _dir = os.path.join(self.real_output, f'{package}')
        if not os.path.exists(_dir):
            os.makedirs(_dir)
        # jks文件
        _jks = os.path.join(_dir, self.keystore)
        command = f'keytool -genkey -v -keystore {_jks} -alias {alias} -storepass {store_pass} -keypass {key_pass} ' \
                  f'-keyalg {key_alg} -keysize {str(key_size)} -validity {str(validity)}'
        print(f'ready to execute cdmstr : {command}')
        # 交互输入开始
        child = pexpect.spawn(command, encoding="UTF-8")
        child.expect("What is your first and last name?")
        child.sendline(package)
        child.expect("What is the name of your organizational unit?")
        child.sendline('SZ')
        child.expect("What is the name of your organization?")
        child.sendline('SZ')
        child.expect("What is the name of your City or Locality?")
        child.sendline('HZ')
        child.expect("What is the name of your State or Province?")
        child.sendline('ZJ')
        child.expect("What is the two-letter country code for this unit?")
        child.sendline('CN')
        child.expect(f'Is CN={package}, OU=SZ, O=SZ, L=HZ, ST=ZJ, C=CN correct?')
        child.sendline("y")
        print("jks path : " + _jks)
        print("waiting for the job done....")
        # 休眠等待文件生成
        time.sleep(2)
        print("move to pkcs12")
        # 迁移行业标准pkcs12
        _shell_pkcs12 = f'keytool -importkeystore -srckeystore {_jks} -destkeystore {_jks} -deststoretype pkcs12'
        print(f'{_shell_pkcs12}')
        pkcs12 = pexpect.spawn(_shell_pkcs12, encoding="UTF-8")
        pkcs12.expect("Enter source keystore password:")
        pkcs12.sendline(key_pass)
        # 休眠等待文件生成
        time.sleep(1)
        _old = f'{_jks}.old'
        if os.path.exists(_old):
            os.remove(_old)
        print("done!")
        return _jks
        pass

    @staticmethod
    def create_txt_info(jks_path: str, txt_name: str, key_pass: str):
        """
        在同文件路径下生成签名信息txt
        :param jks_path 签名文件路径
        :param txt_name txt文件名
        :param key_pass 签名文件密码
        """
        print("start query md5 & sha1 & sha256 ...")
        if not os.path.exists(jks_path):
            print(f'传入的文件路径 >>> {jks_path} 不存在！')
            return None
        path_dicts = jks_path.split('/')
        txt_path = jks_path.replace(f'{path_dicts[len(path_dicts) - 1]}', f'{txt_name}')
        command = f'keytool -v -list -keystore {jks_path}'
        print(f'{command}')
        result = pexpect.spawn(command, encoding="UTF-8")
        result.expect("Enter keystore password:")
        result.sendline(key_pass)
        print("start write file ..." + txt_path)
        txt_file = open(txt_path, "w")
        txt_file.truncate()
        txt_file.write(result.read())
        txt_file.close()
        print("write done!")
        pass

    @staticmethod
    def random_package():
        _center_lenght = random.randint(4, 7)
        _end_lenght = random.randint(5, 8)
        _strlist = list(random.sample('zyxwvutsrqponmlkjihgfedcba', _center_lenght + _end_lenght))
        _strlist.insert(_center_lenght, ".")
        _full_packagename = "com." + "".join(_strlist)
        return _full_packagename

    @staticmethod
    def random_package_list(_size):
        print("need package size --> " + str(_size))
        _package_list = set()
        print("random package generating...")
        while len(_package_list) < _size:
            _new_package = JKSCreate.random_package()
            if _new_package in _package_list:
                _new_package = JKSCreate.random_package()
                pass
            _package_list.add(_new_package)
        print("random package generate compelete!")
        return _package_list
