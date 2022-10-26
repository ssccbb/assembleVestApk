# coding=utf-8
import constants
from git import *

git = Git(constants.path_android)
git.remove_local_change()