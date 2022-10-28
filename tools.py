# coding=utf-8
import os
import sys

import constants
from files.plugin.FilePlugin import FilePlugin
from git import Git


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
            sys.exit(0)
        file_content = f'sdk.dir = {sdk_dir}\nndk.dir = {ndk_dir}'
        FilePlugin.wirte_str_to_file(file_content, local_properties)
        print(f'local.properties 创建成功')
        pass

    @staticmethod
    def rollback():
        git = Git(constants.path_android)
        git.remove_local_change()
        pass


if __name__ == '__main__':
    """
    工具集合入口，自定义选择执行脚本
    """
    print(f'【1】重置huajian-android内的本地properties文件'.join(("\033[7m", "\033[0m")))
    print(f'【2】回退huajian-android所有变更代码'.join(("\033[7m", "\033[0m")))
    try:
        inp = int(input('请输入执行选项：'))
        if inp == 1:
            Entry.reset_properties()
        elif inp == 2:
            Entry.rollback()
    except Exception as e:
        sys.exit(0)
    pass
