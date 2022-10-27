# coding=utf-8
import constants
from git import *
from virus.junkcode.BuildJunkCode import *

git = Git(constants.path_android)
git.remove_local_change()
# b = Builder(constants.path_android, 'com.qwerq.adaa')
# b.creat_junk()
