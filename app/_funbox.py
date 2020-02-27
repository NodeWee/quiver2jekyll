# -*- coding: utf-8 -*-

import os
import sys
import re

PY3 = sys.version_info >= (3, )


def hyphenCase(s):
    return '-'.join(
        re.sub('([A-Z][a-z]+)', r' \1',
               re.sub('([A-Z]+)', r' \1', s.replace('-',
                                                    ' '))).split()).lower()


def rinseStringToEnglishUrl(s):  # 过滤字符串以符合英文 url 格式
    ns = re.sub(r'[^a-zA-Z\d\-]', ' ', s)
    ns = hyphenCase(ns)
    #
    return ns if ns else 'untitled'


def existStringAddSerial(newStr, strList, separator='', _curI=1):
    '''
    please ignore _curI parameter
    '''
    if _curI < 2:
        if newStr not in strList:
            return newStr

    if newStr + separator + str(_curI) not in strList:
        return newStr + separator + str(_curI)

    return existStringAddSerial(newStr, strList, separator, _curI + 1)


def makeDirs(dirpath):
    '''
    创建目录，支持多级目录的创建，若目录已存在自动忽略
    '''

    # 去除首尾空格和右侧的路径分隔符
    dirpath = dirpath.strip().rstrip(os.path.sep)

    if dirpath:
        if not os.path.exists(dirpath):  # 如果目录已存在, 则pass，否则才创建
            os.makedirs(dirpath)


def load_jekyll_post_template(tpl_file_path):
    '''
    载入 jekyll post(.md) 的模板。
    支持的变量：{title}, {uuid}, {tags}, {content}, {created}, {updated}
    '''
    with open(tpl_file_path, 'r') as f:
        data = f.read()
    return data if PY3 else data.decode('utf-8')
