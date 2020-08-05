# -*- coding: utf-8 -*-
"""
convert Quiver notes to Jekyll posts
=====

Project Url: https://github.com/nodewee/quiver2jekyll
Author: nodewee (https://nodewee.github.io)
License: BSD-3-Clause-Clear

-----
Enviroment: Python 3
"""

import os
import sys
import json
import re
import time
import shutil

from _funbox import rinseStringToEnglishUrl, existStringAddSerial, makeDirs

PY3 = sys.version_info >= (3, )


def convert(in_path, out_path, resources_dir_path, resources_url_path,
            post_template, notebook_name_overwrite_list):
    # step 1
    note2PostData, notebookNames = _prepareNotes(in_path)

    # step 2
    note2PostData = _prepareMarkdown(note2PostData, notebookNames, out_path,
                                     resources_dir_path, resources_url_path,
                                     notebook_name_overwrite_list)

    # step 3 | convert .qvnote -> .md
    count = 0
    notes_which_linked_but_no_converting = []

    for nt_uuid in note2PostData:
        qvnote_path = note2PostData[nt_uuid]['note_path']
        markdown_filepath = note2PostData[nt_uuid]['md_filepath']

        content = json.loads(
            open(os.path.join(qvnote_path, u'content.json'), 'r').read())

        md_data = _convert_qvjson_to_jkmd(
            nt_uuid, note2PostData, content, post_template,
            notes_which_linked_but_no_converting)
        # -save md data to file
        makeDirs(os.path.dirname(markdown_filepath))
        with open(os.path.join(markdown_filepath), 'wb') as f:
            f.write(md_data.encode('utf-8'))
            count += 1
    # end for

    if len(notes_which_linked_but_no_converting) > 0:
        print('linked notes but not in converting list:')
        for s in notes_which_linked_but_no_converting:
            print('\t' + s)

    return count


def _prepareNotes(in_path, draft_sign='_'):
    '''
    STEP 1
    qvnotes' file path
    '''
    note2PostData = {}
    notebookNames = {}

    in_path = in_path.rstrip('/')
    if not os.path.isdir(in_path):
        return note2PostData, notebookNames

    [_, inPath_extName] = os.path.splitext(in_path)

    if inPath_extName == '.qvnote':
        # check note title,
        meta = json.loads(
            open(os.path.join(in_path, u'meta.json'), 'r').read())
        note_title = meta['title']
        # if title string starts with draft sign(default "_")
        if note_title.startswith(draft_sign):
            return note2PostData, notebookNames  # consider it's a draft, so not convert

        # base_name is note uuid
        nt_uuid, _ = os.path.splitext(os.path.split(in_path)[1])
        note2PostData[nt_uuid] = {'note_path': in_path}
        return note2PostData, notebookNames

    if inPath_extName == '.qvnotebook':
        ntbk_uuid, _ = os.path.splitext(os.path.split(in_path)[1])

        # filter Trash.qvnotebook
        if ntbk_uuid.lower() == u"trash":
            return note2PostData, notebookNames

        ntbk_meta = json.loads(
            open(os.path.join(in_path, u'meta.json'), 'r').read())

        # if notebook name starts with draft sign(default "_")
        if ntbk_meta['name'].startswith(draft_sign):
            return note2PostData, notebookNames  # consider it's a draft, so not convert

        # notebook uuid mapping name
        notebookNames[ntbk_uuid] = ntbk_meta['name']

        # notes in notebook
        for dir_name in os.listdir(in_path):
            nt_path = os.path.join(in_path, dir_name)
            # merge sub notes to all
            sub_notesUri, _ = _prepareNotes(nt_path)
            note2PostData = {**note2PostData, **sub_notesUri}
        #
        return note2PostData, notebookNames

    if inPath_extName == ".qvlibrary":
        for dir_name in os.listdir(in_path):  # maybe notebooks in library
            maybe_ntbk_path = os.path.join(in_path, dir_name)
            # merge subs to all
            sub_notesUri, sub_notebooksName = _prepareNotes(maybe_ntbk_path)
            note2PostData = {**note2PostData, **sub_notesUri}
            notebookNames = {**notebookNames, **sub_notebooksName}
        #
        return note2PostData, notebookNames

    return note2PostData, notebookNames


def _prepareMarkdown(note2PostData, notebookNames, out_path,
                     resources_dir_path, resources_url_path,
                     notebook_name_overwrite_list):
    '''
    STEP 2
    md file path, and post data
    '''
    existMarkdownFileTitle = []
    for nt_uuid in note2PostData:
        nt_path = note2PostData[nt_uuid]['note_path']

        # notebook (note belongs to) name
        ntbk_name = ""
        [ntbk_uuid, parent_extName
         ] = os.path.splitext(os.path.basename(os.path.dirname(nt_path)))
        if parent_extName != ".qvnotebook":
            ntbk_name = "untitle_notebook"
        else:
            if ntbk_uuid in notebookNames:
                ntbk_name = notebookNames[ntbk_uuid]
            else:
                # notebook uuid mapping name
                ntbk_path = os.path.dirname(nt_path)
                ntbk_meta = json.loads(
                    open(os.path.join(ntbk_path, u'meta.json'), 'r').read())
                notebookNames[ntbk_uuid] = ntbk_meta['name']
                #
                ntbk_name = notebookNames[ntbk_uuid]

        # read qvnote's meta data form meta.json
        meta = json.loads(
            open(os.path.join(nt_path, u'meta.json'), u'rt',
                 encoding=u'utf-8').read())

        # read Q2J post config from first cell which type is markdown,
        # and add config data to meta data dict
        content = json.loads(
            open(os.path.join(nt_path, u'content.json'),
                 u'rt',
                 encoding=u'utf-8').read())
        if len(content[u'cells']) > 0:
            if content[u'cells'][0]['type'] == 'markdown':

                first_cell_data = content[u'cells'][0]['data']
                # 每篇文章的可配置项

                # option : user custome md filename
                matched = re.search(r'\{mdfn:(.*?)\}', first_cell_data)
                if matched:
                    meta['user_custom_md_filename'] = matched.groups(
                    )[0].strip()
                    meta['user_custom_md_filename'] = rinseStringToEnglishUrl(
                        meta['user_custom_md_filename'])
                # option : user custome post description
                matched = re.search(r'\{desc:(.*?)\}', first_cell_data)
                if matched:
                    meta['user_custom_post_description'] = matched.groups(
                    )[0].strip()
                # option | comments switch (for discus)
                matched = re.search(r'\{comments:(.*?)\}', first_cell_data)
                if matched:
                    meta['user_custom_comments_switch'] = matched.groups(
                    )[0].strip()

        #
        note2PostData[nt_uuid]['meta'] = meta

        # - md filename (date part & title part)
        md_filename_date = time.strftime(
            u"%Y-%m-%d", time.localtime(meta.get(u'created_at')))
        md_filename_title = meta.get('user_custom_md_filename')
        if not md_filename_title:
            md_filename_title = rinseStringToEnglishUrl(
                meta.get("title")).lower()
        md_filename_title = existStringAddSerial(md_filename_title,
                                                 existMarkdownFileTitle, '-')
        existMarkdownFileTitle.append(
            md_filename_title)  # cache exist md file title

        if ntbk_name:
            if ntbk_name in notebook_name_overwrite_list:  # overwrite ntbk_name
                ntbk_name = notebook_name_overwrite_list[ntbk_name]

        # - md file path
        md_dir_relpath = ""
        md_dir_relpath = os.path.join(md_dir_relpath, ntbk_name)
        note2PostData[nt_uuid]['md_filepath'] = os.path.join(
            out_path, md_dir_relpath,
            md_filename_date + '-' + md_filename_title + '.md')

        # - post url
        url_subdirname = ''
        if ntbk_name == '_posts':
            pass  # url_subdirname = ''
        else:  # is collection dir
            url_subdirname = ntbk_name.lstrip('_')
        #
        note2PostData[nt_uuid]['post_url'] = '/' + '/'.join(
            [url_subdirname, md_filename_title]) + '.html'

        # - resources dir path
        note_created_year = time.strftime(
            u"%Y" + os.path.sep + u"%m",
            time.localtime(meta.get(u'created_at')))
        note2PostData[nt_uuid]['md_resources_dir_path'] = os.path.join(
            resources_dir_path, note_created_year)
        # - resources dir url
        note2PostData[nt_uuid]['md_resources_dir_url'] = '/'.join(
            [resources_url_path, note_created_year])

    return note2PostData


def _convert_qvjson_to_jkmd(note_uuid, notes2post_data, content, post_template,
                            notes_which_linked_but_no_converting):
    '''
    STEP 3
    convert quiver json content to jekyll markdown content
    '''
    meta = notes2post_data[note_uuid]['meta']
    title = meta.get(u'title')
    created = time.strftime(u"%Y-%m-%d",
                            time.localtime(meta.get(u'created_at')))
    updated = time.strftime(u"%Y/%m/%d",
                            time.localtime(meta.get(u'updated_at')))
    # print(updated)
    tags = ''
    for tag in meta.get(u'tags'):
        tags += "\n - " + tag
    description = meta.get('user_custom_post_description')
    if not description:
        description = ''

    comments_switch = meta.get('user_custom_comments_switch')
    if comments_switch is None:
        comments_switch = 'true'

    # clear user custom Q2J post config (in first cell which type is markdown
    if content.get(u'cells'):
        if content[u'cells'][0]['type'] == 'markdown':
            tmpd = content[u'cells'][0]['data']
            tmpd = re.sub(r'\{mdfn:(.*?)\}', '', tmpd)
            tmpd = re.sub(r'\{desc:(.*?)\}', '', tmpd)
            tmpd = re.sub(r'\{comments:(.*?)\}', '', tmpd)
            content[u'cells'][0]['data'] = tmpd

    #
    new_content = u''
    for cell in content[u'cells']:
        if cell['type'] in ['text', 'markdown']:
            tmpdata = cell['data']
            # convert links
            tmpdata = _convert_qvcell_resourceLinks(tmpdata, note_uuid,
                                                    notes2post_data)
            tmpdata = _convert_qvcell_noteLinks(
                tmpdata, notes2post_data, notes_which_linked_but_no_converting)

            tmpdata = _convert_filter_x_callback_url(tmpdata)
            # markdown format
            if cell['type'] == 'markdown':
                tmpdata = _convert_qvcell_markdown_format(tmpdata)
            #
            new_content += u'\n' + tmpdata + u'\n'
        elif cell['type'] == 'code':
            new_content += u'\n~~~ ' + cell['language'] + \
                u'\n' + cell['data'] + u'\n~~~\n'
        elif cell['type'] == 'latex':
            new_content += u'\n$$\n' + cell['data'] + '\n$$\n'
        else:
            new_content += u'\n' + cell['data'] + u'\n'
    # end for

    jekyllmd = post_template.format(title=title,
                                    content=new_content,
                                    uuid=note_uuid,
                                    tags=tags,
                                    created=created,
                                    updated=updated,
                                    description=description,
                                    comments_switch=comments_switch)
    return jekyllmd


def _convert_qvcell_markdown_format(cell_data):
    '''
        方法有点笨，管用先行
    '''
    lines = cell_data.splitlines()
    line_in_mode = 'normal'
    line_last_mode = 'normal'
    last_is_blank = False

    new_lines = []
    for line in lines:
        trimline = line.strip()

        if trimline.startswith(('```', '~~~')):
            if line_last_mode == 'precode_in':
                line_in_mode = 'precode_out'
            else:
                line_in_mode = 'precode_in'
        else:
            if line_last_mode == 'precode_in':
                line_in_mode = 'precode_in'
            else:
                if trimline.startswith('#'):
                    line_in_mode = 'headline'
                elif trimline.startswith('>'):
                    line_in_mode = 'blockquote'
                elif trimline.startswith(('- ', '* ')):
                    line_in_mode = 'ul'
                elif trimline.startswith(('-', '*', '_')):
                    if len(trimline
                           ) > 2 and trimline == trimline[0] * len(trimline):
                        line_in_mode = 'hr'
                    else:
                        if last_is_blank:
                            line_in_mode = 'normal'
                        else:
                            line_in_mode = line_last_mode
                elif trimline.startswith('|'):
                    line_in_mode = 'table'
                elif trimline == '':  # empty line
                    if line_last_mode in ['ul', 'ul_subtext']:
                        if not last_is_blank:
                            line_in_mode = 'ul_subtext'
                        else:
                            line_in_mode = 'normal'
                    else:
                        line_in_mode = 'normal'
                else:
                    if line_last_mode in ['ul']:
                        line_in_mode = 'ul_subtext'
                    elif line_last_mode in ['ul_subtext']:
                        if last_is_blank:
                            line_in_mode = 'normal'
                        else:
                            line_in_mode = 'ul_subtext'
                    elif line_last_mode in ['precode_out', 'hr']:
                        line_in_mode = 'normal'
                    else:
                        line_in_mode = 'normal'

        # new line
        # print(line_in_mode, '|', trimline)
        if trimline == '':
            if line_in_mode == 'ul_subtext':
                new_line = '&nbsp;'
            else:
                new_line = ''
        else:
            if line_in_mode == 'headline':
                new_line = '\n' + line
            elif line_in_mode == 'ul_subtext':
                new_line = '&emsp;&emsp;' + line

                if line_last_mode == 'ul':
                    new_lines[len(new_lines) - 1] += '  '
            elif line_last_mode == 'ul_subtext' and last_is_blank and line_in_mode == 'normal':
                new_line = '\n' + line
            else:
                if line_in_mode == 'table' and line_last_mode != 'table':
                    new_line = '\n' + line
                elif line_in_mode == 'hr':
                    new_line = '<hr />'
                else:
                    new_line = line
        #
        new_lines.append(new_line)

        #
        line_last_mode = line_in_mode
        if trimline == '':
            last_is_blank = True
        else:
            last_is_blank = False

    # end for lines

    #
    new_cell = '\n'.join(new_lines)

    # return
    return new_cell


def _convert_qvcell_resourceLinks(cell_data, note_uuid, notes2post_data):
    def _one_type_links(cell_data, note_uuid, notes2post_data, link_pattern,
                        filename_pattern):
        qvResource_links = re.findall(link_pattern, cell_data)
        qvResource_links = list(set(qvResource_links))
        for resLink in qvResource_links:
            resource_filename = re.findall(filename_pattern, resLink)[0]
            # copy resource file
            path_srcFile = os.path.join(
                notes2post_data[note_uuid]['note_path'], "resources",
                resource_filename)
            path_destFile = os.path.join(
                notes2post_data[note_uuid]['md_resources_dir_path'],
                resource_filename)
            makeDirs(os.path.dirname(path_destFile))
            shutil.copyfile(path_srcFile, path_destFile)

            # replace link
            new_resLink = '/'.join([
                notes2post_data[note_uuid]['md_resources_dir_url'],
                resource_filename
            ])
            print(new_resLink)
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
    cell_data = _one_type_links(cell_data, note_uuid, notes2post_data,
                                r'\(quiver-image-url\/.*?\)',
                                r'\(quiver-image-url\/(.*?)[\s|\)]')
    cell_data = _one_type_links(cell_data, note_uuid, notes2post_data,
                                r'\(quiver-file-url\/.*?\)',
                                r'\(quiver-file-url\/(.*?)[\s|\)]')
    cell_data = _one_type_links(cell_data, note_uuid, notes2post_data,
                                r"src=['|\"]quiver-image-url/.*?['|\"]",
                                r"src=['|\"]quiver-image-url/(.*?)['|\"]")
    cell_data = _one_type_links(cell_data, note_uuid, notes2post_data,
                                r"href=['|\"]quiver-file-url/.*?['|\"]",
                                r"href=['|\"]quiver-file-url/(.*?)['|\"]")
    return cell_data


def _convert_qvcell_noteLinks(cell_data, notes2post_data,
                              notes_which_linked_but_no_converting):
    notes_which_linked_but_no_converting = notes_which_linked_but_no_converting

    def _one_type_links(cell_data, notes2post_data, link_pattern,
                        linkNoteUUID_pattern):
        noteLinks = re.findall(link_pattern, cell_data)
        noteLinks = list(set(noteLinks))
        for link in noteLinks:
            noteUUID = re.findall(linkNoteUUID_pattern, link)[0]
            if noteUUID in notes2post_data.keys():
                new_link = "(" + notes2post_data[noteUUID]['post_url'] + ")"
            else:
                new_link = '()'
                if noteUUID not in notes_which_linked_but_no_converting:
                    notes_which_linked_but_no_converting.append(noteUUID)
            # replace link
            cell_data = cell_data.replace(link, new_link)
        return cell_data

    #
    cell_data = _one_type_links(
        cell_data,
        notes2post_data,
        r'\(quiver-note-url/.*?\)',
        # supported url example: (quiver-note-url/87AB5ED5-C1A5-45F5-95A3-667C9B2CD0B6#parameter)
        r'\(quiver-note-url/([A-Z0-9\-]+).*\)',
    )

    return cell_data


def _convert_filter_x_callback_url(cell_data):
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
