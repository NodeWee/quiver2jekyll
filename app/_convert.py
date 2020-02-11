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
import json
import re
import time
import shutil

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


def convert(in_path, out_path, resources_dir_path, post_template,
            notebook_name_overwrite_list):
    allNotesUri, allNotebooksName = _prepareNotes(in_path)

    allNotesUri = _prepareMarkdown(allNotesUri, allNotebooksName, out_path,
                                   resources_dir_path,
                                   notebook_name_overwrite_list)

    # convert .qvnote -> .md
    count = 0
    for nt_uuid in allNotesUri:
        qvnote_path = allNotesUri[nt_uuid]['note_path']
        markdown_filepath = allNotesUri[nt_uuid]['md_filepath']

        # - convert data
        # read note meta & content from .json file
        meta = json.loads(
            open(os.path.join(qvnote_path, u'meta.json'), 'r').read())
        content = json.loads(
            open(os.path.join(qvnote_path, u'content.json'), 'r').read())

        md_data = _convert_qvjson_to_jkmd(meta, content, post_template,
                                          allNotesUri)
        # -save md data to file
        makeDirs(os.path.dirname(markdown_filepath))
        with open(os.path.join(markdown_filepath), 'wb') as f:
            f.write(md_data.encode('utf-8'))
            count += 1

    return count


def _prepareNotes(in_path, draft_sign='_'):
    '''
    准备所有笔记：文件的源路径
    '''
    allNotesUri = {}
    allNotebooksName = {}

    in_path = in_path.rstrip('/')
    if not os.path.isdir(in_path):
        return allNotesUri, allNotebooksName

    [_, inPath_extName] = os.path.splitext(in_path)

    if inPath_extName == '.qvnote':
        # check note title,
        meta = json.loads(
            open(os.path.join(in_path, u'meta.json'), 'r').read())
        note_title = meta['title']
        # if title string starts with draft sign(default "_")
        if note_title.startswith(draft_sign):
            return allNotesUri, allNotebooksName  # consider it's a draft, so not convert

        # base_name is note uuid
        nt_uuid, _ = os.path.splitext(os.path.split(in_path)[1])
        allNotesUri[nt_uuid] = {'note_path': in_path}
        return allNotesUri, allNotebooksName

    if inPath_extName == '.qvnotebook':
        ntbk_uuid, _ = os.path.splitext(os.path.split(in_path)[1])

        # filter Trash.qvnotebook
        if ntbk_uuid.lower() == u"trash":
            return allNotesUri, allNotebooksName

        ntbk_meta = json.loads(
            open(os.path.join(in_path, u'meta.json'), 'r').read())

        # if notebook name starts with draft sign(default "_")
        if ntbk_meta['name'].startswith(draft_sign):
            return allNotesUri, allNotebooksName  # consider it's a draft, so not convert

        # notebook uuid mapping name
        allNotebooksName[ntbk_uuid] = ntbk_meta['name']

        # notes in notebook
        for dir_name in os.listdir(in_path):
            nt_path = os.path.join(in_path, dir_name)
            # merge sub notes to all
            sub_notesUri, _ = _prepareNotes(nt_path)
            allNotesUri = {**allNotesUri, **sub_notesUri}
        #
        return allNotesUri, allNotebooksName

    if inPath_extName == ".qvlibrary":
        for dir_name in os.listdir(in_path):  # maybe notebooks in library
            maybe_ntbk_path = os.path.join(in_path, dir_name)
            # merge subs to all
            sub_notesUri, sub_notebooksName = _prepareNotes(maybe_ntbk_path)
            allNotesUri = {**allNotesUri, **sub_notesUri}
            allNotebooksName = {**allNotebooksName, **sub_notebooksName}
        #
        return allNotesUri, allNotebooksName

    return allNotesUri, allNotebooksName


def _prepareMarkdown(allNotesUri, allNotebooksName, out_path,
                     resources_dir_path, notebook_name_overwrite_list):
    '''
    准备所有的目的路径
    '''
    existMarkdownFileTitle = []
    for nt_uuid in allNotesUri:
        nt_path = allNotesUri[nt_uuid]['note_path']

        # notebook (note belongs to) name
        ntbk_name = ""
        [ntbk_uuid, parent_extName
         ] = os.path.splitext(os.path.basename(os.path.dirname(nt_path)))
        if parent_extName != ".qvnotebook":
            ntbk_name = "untitle_notebook"
        else:
            if ntbk_uuid in allNotebooksName:
                ntbk_name = allNotebooksName[ntbk_uuid]
            else:
                # notebook uuid mapping name
                ntbk_path = os.path.dirname(nt_path)
                ntbk_meta = json.loads(
                    open(os.path.join(ntbk_path, u'meta.json'), 'r').read())
                allNotebooksName[ntbk_uuid] = ntbk_meta['name']
                #
                ntbk_name = allNotebooksName[ntbk_uuid]

        # qvnote meta data
        meta = json.loads(
            open(os.path.join(nt_path, u'meta.json'), u'rt',
                 encoding=u'utf-8').read())
        note_created_at = meta.get(u'created_at')

        # md file name - date
        md_filename_date = time.strftime(u"%Y-%m-%d",
                                         time.localtime(note_created_at))
        # md file name - title
        md_filename_title = ''
        # - if user custom file name in the first line of content
        content = json.loads(
            open(os.path.join(nt_path, u'content.json'),
                 u'rt',
                 encoding=u'utf-8').read())
        if len(content[u'cells']) > 0:
            if content[u'cells'][0]['type'] == 'markdown':
                first_cell_data = content[u'cells'][0]['data']
                # first_cell_data = re.sub(r'<.*?>',"",first_cell_data) #find in html
                match = re.search(r'\{mdfn:(.*?)\}', first_cell_data)
                if match:
                    user_custom_md_filename = match.groups()[0].strip()
                    md_filename_title = rinseStringToEnglishUrl(
                        user_custom_md_filename)
        if md_filename_title == '':  # - else, use note title as md file name
            md_filename_title = rinseStringToEnglishUrl(
                meta.get("title")).lower()
        #
        md_filename_title = existStringAddSerial(md_filename_title,
                                                 existMarkdownFileTitle, '-')
        existMarkdownFileTitle.append(md_filename_title)

        if ntbk_name:
            if ntbk_name in notebook_name_overwrite_list:  # overwrite ntbk_name
                ntbk_name = notebook_name_overwrite_list[ntbk_name]

        # - md file path
        md_dir_relpath = ""
        md_dir_relpath = os.path.join(md_dir_relpath, ntbk_name)
        allNotesUri[nt_uuid]['md_filepath'] = os.path.join(
            out_path, md_dir_relpath,
            md_filename_date + '-' + md_filename_title + '.md')
        # - post url
        url_subdirname = ''
        if ntbk_name == '_posts':
            pass  # url_subdirname = ''
        else:  # is collection dir
            url_subdirname = ntbk_name.lstrip('_')
        allNotesUri[nt_uuid]['post_url'] = '/' + \
            '/'.join([url_subdirname, md_filename_title])

        # - resources dir path
        note_created_year = time.strftime(u"%Y" + os.path.sep + u"%m",
                                          time.localtime(note_created_at))
        allNotesUri[nt_uuid]['md_resources_dir_path'] = os.path.join(
            resources_dir_path, note_created_year)
        # - resources dir url
        allNotesUri[nt_uuid]['md_resources_dir_url'] = '/' + \
            '/'.join(['resources', note_created_year])

    return allNotesUri


def _convert_qvjson_to_jkmd(meta, content, post_template, all_note_uri):
    """ quiver json content to jekyll markdown content """

    note_uuid = meta.get(u'uuid')
    title = content.get(u'title')
    created = time.strftime(u"%Y-%m-%d",
                            time.localtime(content.get(u'created_at')))
    updated = time.strftime(u"%Y-%m-%d",
                            time.localtime(content.get(u'created_at')))
    tags = ""
    for tag in meta.get(u'tags'):
        tags += "\n - " + tag
    # md_resources_dir_path = all_note_uri[note_uuid]['md_resources_dir_path']

    # clear custom jekyll file name block in first cell block
    if content.get(u'cells'):
        if content[u'cells'][0]['type'] == 'markdown':
            content[u'cells'][0]['data'] = re.sub(r'\{mdfn:(.*?)\}', '',
                                                  content[u'cells'][0]['data'])
    #
    new_content = u''
    for cell in content[u'cells']:
        if cell['type'] in ['text', 'markdown']:
            tmpdata = cell['data']
            # convert links
            tmpdata = _convert_qvcell_resourceLinks(tmpdata, note_uuid,
                                                    all_note_uri)
            tmpdata = _convert_qvcell_noteLinks(tmpdata, all_note_uri)
            tmpdata = _filter_x_callback_url(tmpdata)
            # markdown format
            if cell['type'] == 'markdown':
                # ul li 有空行后，格式不兼容处理
                tmpdata = re.sub(r'(\n)(\n\* )', r'\1&nbsp;\2', tmpdata)
                tmpdata = re.sub(r'(\n)(\n\- )', r'\1&nbsp;\2', tmpdata)

                # 单个换行符号后添加两个空格
                r = re.findall(r'([^\n]\n[^\n])', tmpdata)
                for s in r:
                    tmpdata = tmpdata.replace(s, s.replace('\n', '  \n'))

            #
            new_content += u'\n' + tmpdata + u'\n'
        elif cell['type'] == 'code':
            new_content += u'\n~~~ ' + cell['language'] + \
                u'\n' + cell['data'] + u'\n~~~\n'
        elif cell['type'] == 'latex':
            new_content += u'\n$$\n' + cell['data'] + '\n$$\n'
        else:
            new_content += u'\n' + cell['data'] + u'\n'

    jekyllmd = post_template.format(title=title,
                                    content=new_content,
                                    uuid=note_uuid,
                                    tags=tags,
                                    created=created,
                                    updated=updated)
    return jekyllmd


def _convert_qvcell_resourceLinks(cell_data, note_uuid, all_note_uri):
    def _one_type_links(cell_data, note_uuid, all_note_uri, link_pattern,
                        filename_pattern):
        qvResource_links = re.findall(link_pattern, cell_data)
        qvResource_links = list(set(qvResource_links))
        for resLink in qvResource_links:
            resource_filename = re.findall(filename_pattern, resLink)[0]
            # copy resource file
            path_srcFile = os.path.join(all_note_uri[note_uuid]['note_path'],
                                        "resources", resource_filename)
            path_destFile = os.path.join(
                all_note_uri[note_uuid]['md_resources_dir_path'],
                resource_filename)
            makeDirs(os.path.dirname(path_destFile))
            shutil.copyfile(path_srcFile, path_destFile)

            # replace link
            new_resLink = '/'.join([
                all_note_uri[note_uuid]['md_resources_dir_url'],
                resource_filename
            ])
            if link_pattern.startswith("src="):
                new_resLink = "src=\"" + new_resLink + "\""
            elif link_pattern.startswith("href="):
                new_resLink = "href=\"" + new_resLink + "\""
            elif link_pattern.startswith(r"\("):
                new_resLink = '(' + new_resLink + ')'
            else:
                print('WRONG: unkown link_pattern:', link_pattern)
                new_resLink = None
                continue
            #
            cell_data = cell_data.replace(resLink, new_resLink)

        return cell_data

    #
    cell_data = _one_type_links(cell_data, note_uuid, all_note_uri,
                                r'\(quiver-image-url\/.*?\)',
                                r'\(quiver-image-url\/(.*?)[\s|\)]')
    cell_data = _one_type_links(cell_data, note_uuid, all_note_uri,
                                r'\(quiver-file-url\/.*?\)',
                                r'\(quiver-file-url\/(.*?)[\s|\)]')
    cell_data = _one_type_links(cell_data, note_uuid, all_note_uri,
                                r"src=['|\"]quiver-image-url/.*?['|\"]",
                                r"src=['|\"]quiver-image-url/(.*?)['|\"]")
    cell_data = _one_type_links(cell_data, note_uuid, all_note_uri,
                                r"href=['|\"]quiver-file-url/.*?['|\"]",
                                r"href=['|\"]quiver-file-url/(.*?)['|\"]")
    return cell_data


#


def _convert_qvcell_noteLinks(cell_data, all_note_uri):
    def _one_type_links(cell_data, all_note_uri, link_pattern,
                        linkNoteUUID_pattern):
        noteLinks = re.findall(link_pattern, cell_data)
        noteLinks = list(set(noteLinks))
        for link in noteLinks:
            noteUUID = re.findall(linkNoteUUID_pattern, link)[0]
            new_link = "(" + all_note_uri[noteUUID]['post_url'] + ")"
            # replace link
            cell_data = cell_data.replace(link, new_link)
        return cell_data

    #
    cell_data = _one_type_links(cell_data, all_note_uri,
                                r'\(quiver-note-url/.*?\)',
                                r'\(quiver-note-url/(.*?)\)')

    return cell_data


def _filter_x_callback_url(cell_data):
    link_pattern = r'\[(.*?)\]\(x\-.*?:\/\/.*?\)'
    while True:
        r = re.search(link_pattern, cell_data)
        if not r:
            break
        #
        cell_data = cell_data[:r.span()[0]] + r.groups()[0] + cell_data[r.span(
        )[1]:]
    #
    return cell_data
