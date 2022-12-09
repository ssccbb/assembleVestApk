# coding=utf-8
import sys
import builder
import configparser

if __name__ == '__main__':
    print('开始进行打包前的配置确认....')
    config = configparser.ConfigParser()
    config.read(filenames='./release.ini')
    need_regular = config.getboolean('yr', 'need_regular')
    need_base_apk = config.getboolean('yr', 'need_base_apk')
    need_jiagu = config.getboolean('yr', 'need_yd_jiagu')
    base_version_name = str(config.get('yr', 'base_version_name'))
    log_txt = str(config.get('log', 'log'))
    package_list = {}
    for package in config.options('packages'):
        package_list.update({package: config.get('packages', package)})
    if package_list is None or len(package_list) == 0:
        print('ERROR! 请检查 release.ini 配置文件！\n')
        sys.exit(0)
    print(f'配置确认成功！即将开始打包任务 >>> {package_list}')
    # 打包流程
    job = builder.ReleaseBuilder(need_regular, need_base_apk, base_version_name, package_list, need_jiagu, log_txt)
    job.assemble_list_()
    pass
