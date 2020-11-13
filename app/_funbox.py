# -*- coding: utf-8 -*-
"""
    Project: https://github.com/nodewee/quiver2jekyll
    Author: nodewee (https://nodewee.github.io)
    License: Apache License 2.0
"""

import os
import sys
import re

PY3 = sys.version_info >= (3, )


def clear_english_punctuation(text, replace_char=""):
    '''
    Update: 2020-08-07
    '''
    import string
    find_chars = string.punctuation + string.whitespace
    for fchar in find_chars:
        text = text.replace(fchar, replace_char)

    return text


def clear_chinese_punctuation(text, replace_char=""):
    find_chars = '　－。，、＇：∶；?‘’“”〝〞ˆˇ﹕︰﹔﹖﹑·¨….¸;！´？！～—ˉ｜‖＂〃｀@﹫¡¿﹏﹋﹌︴々﹟#﹩$﹠&﹪%*﹡﹢﹦﹤‐￣¯―﹨ˆ˜﹍﹎+=<··＿_-\ˇ~﹉﹊（）〈〉‹›﹛﹜『』〖〗［］《》〔〕「」【】︵︷︿︹︽_﹁﹃︻︶︸﹀︺︾ˉ﹂﹄︼'  # 中文标点符号
    for fchar in find_chars:
        text = text.replace(fchar, replace_char)

    return text


def rinse_string_to_url_slug(s):
    slug = re.sub(r'[^a-zA-Z\d\-]', '-', s)
    slug = hyphenCase(slug)
    slug = re.sub(r'-+', '-', slug)
    return slug


def hyphenCase(s):
    return '-'.join(
        re.sub('([A-Z][a-z]+)', r' \1',
               re.sub('([A-Z]+)', r' \1', s.replace('-',
                                                    ' '))).split()).lower()


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
