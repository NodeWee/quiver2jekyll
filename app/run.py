# -*- coding: utf-8 -*-
"""
convert Quiver notes to Jekyll posts
=====

Project Url: https://github.com/nodewee/quiver2jekyll
License: BSD-3-Clause-Clear
Copyright (c) 2020 nodewee(nodewee@gmail.com)
All rights reserved.

-----
Enviroment: Python 3
"""

import os
import sys
import argparse
import _export as export

PY3 = sys.version_info >= (3, )
''' shell command configuration '''
parser = argparse.ArgumentParser(
    description='Convert quiver notes to jekyll posts.')
parser.add_argument(
    'input_path',
    help='Directory path that is .qvlibrary/.qvnotebook/.qvnote.'
    'Will convert all found qvnotes in the path')
parser.add_argument('output_dir',
                    help='Directory path to save the output jekyll markdown.')
parser.add_argument(
    '-t',
    metavar="FILE_PATH",
    dest="tpl_path",
    help='jekyll markdown template. Deault: template/post.md '
    r'Supported variable in template: {title}, {uuid}, {tags}, {content}, {created}, {updated}')
parser.add_argument('-n',
                    nargs=1,
                    metavar="NOTEBOOK_NAMES",
                    dest="notebook_names",
                    help='overwrite notebook name. Example:'
                    ' -n Category1=category1,Category2=collection2')


''' init path '''
app_path = os.path.dirname(os.path.realpath(__file__))


def main(args):
    # load template
    tpl_path = args.tpl_path if args.tpl_path else os.path.join(
        app_path, 'template/post.md')
    post_template = export.load_jekyll_post_template(
        tpl_path)  # default to load template/post.md

    notebook_name_overwrite_list = {}
    if args.notebook_names:
        for item in args.notebook_names[0].split(','):
            name_pair = item.split("=")
            notebook_name_overwrite_list[
                name_pair[0].strip()] = name_pair[1].strip()

    count = export.convert(args.input_path, args.output_dir, post_template,
                           notebook_name_overwrite_list)
    if count:
        print("Export: {} note(s)".format(count))
    else:
        print("Nothing to export.")

    # print(notebook_name_overwrite_list)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
