#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import getopt
import re
import os
import gzip
import zipfile

from lxml import etree
from lxml import objectify
from lxml import html
import lxml
from lxml.builder import E

import epub
import common

import iarchive

from debug import debug, debugging, assert_d

def process_book(iabook, ebook):
    aby_ns="{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}"
    scandata = iabook.get_scandata()
    aby_file = iabook.get_abbyy()

    bookData = scandata.find('bookData')
    # XXX should fix below and similar by ensuring that scandata is always the same fmt...
    # scandata.zip/scandata.xml parses different?
    if bookData is None:
        bookData = scandata.bookData

    # some books no scanlog
#     scanLog = scandata.find('scanLog')
#     if scanLog is None:
#         scanLog = scandata.scanLog

    i = 0
    part_number = 0
    cover_number = 0
    nav_number = 0
    context = etree.iterparse(aby_file,
                              tag=aby_ns+'page',
                              resolve_entities=False)
    found_title = False
    for page_scandata in iabook.get_scandata_pages(): #confirm title exists
        t = page_scandata.pageType.text
        if t == 'Title' or t == 'Title Page':
            found_title = True
            break
    # True if no title found, else False now, True later.
    before_title_page = found_title
    for event, page in context:
        page_scandata = iabook.get_page_scandata(i)

        pageno = page_scandata.find('pageNumber')
        if pageno:
            part_str = 'part' + str(part_number).zfill(4)
            id = 'page-' + str(pageno)
            page_mark_href = part_str + '.html#' + id
            pdiv = E.div({ 'class':'newpage', 'id':'page-' + str(pageno) })
#             paragraphs.append(pdiv)
            ebook.add_page_item(str(pageno), pageno, page_mark_href)

        def include_page(page_scandata):
            if page_scandata is None:
                return False
            add = page_scandata.find('addToAccessFormats')
            if add is None:
                add = page_scandata.addToAccessFormats
            if add is not None and add.text == 'true':
                return True
            else:
                return False
        if not include_page(page_scandata):
            i += 1
            continue
        page_type = page_scandata.pageType.text.lower()
        if page_type == 'cover':
            pass

        elif page_type == 'title' or page_type == 'title page':
            before_title_page = False
            pass

        elif page_type == 'copyright':
            pass

        elif page_type == 'contents':
            pass

        elif page_type == 'normal':
            if before_title_page:
                pass
                # XXX consider skipping if blank + no words?
                # make page image
#                 (id, filename) = make_html_page_image(i, iabook, ebook)
            else:
                first_par = True
                for block in page:
                    if block.get('blockType') == 'Text':
                        pass
                    else:
                        pass
                    for el in block:
                        if el.tag == aby_ns+'region':
                            for rect in el:
                                pass
                        elif el.tag == aby_ns+'text':
                            for par in el:
                                def par_is_header(par):
                                    # if:
                                    #   it's the first on the page
                                    #   there's only one line
                                    #   on that line, there's a formatting tag, s.t.
                                    #   - it has < 6 charParam kids
                                    #   - each is wordNumeric
                                    # then:
                                    #   Skip it!
                                    if len(par) != 1:
                                        return False
                                    line = par[0]
                                    for fmt in line:
                                        if len(fmt) > 6:
                                            continue
                                        saw_non_num = False
                                        for cp in fmt:
                                            if cp.get('wordNumeric') != 'true':
                                                saw_non_num = True
                                                break
                                        if not saw_non_num:
                                            return True
                                        hdr_text = etree.tostring(fmt,
                                                              method='text',
                                                              encoding=unicode)
                                        rnums = ['i', 'ii', 'iii', 'iv',
                                                 'v', 'vi', 'vii', 'viii',
                                                 'ix', 'x', 'xi', 'xii',
                                                 'xiii', 'xiv', 'xv', 'xvi',
                                                 'xvii', 'xviii', 'xix', 'xx',
                                                 'xxi', 'xxii',
                                                 ]
                                        if hdr_text in rnums:
                                            return True
                                    return False
                                if first_par and par_is_header(par):
                                    first_par = False
                                    continue
                                first_par = False
                                lines = []
                                prev_line = ''
                                for line in par:
                                    for fmt in line:
                                        fmt_text = etree.tostring(fmt,
                                                                  method='text',
                                                                  encoding=unicode)
                                        if len(fmt_text) > 0:
                                            if prev_line[-1:] == '-':
                                                if fmt[0].get('wordStart') == 'false':
                                                    # ? and wordFromDictionary = true ?
                                                    lines.append(prev_line[:-1])
                                                else:
                                                    lines.append(prev_line)
                                            else:
                                                lines.append(prev_line)
                                                lines.append(' ')
                                            prev_line = fmt_text
                                lines.append(prev_line)
#                                 paragraphs.append(E.p(''.join(lines)))
                        elif (el.tag == aby_ns+'row'):
                            pass
                        else:
                            print('unexpected tag type' + el.tag)
                            sys.exit(-1)

        page.clear()
        i += 1

if __name__ == '__main__':
    sys.stderr.write('I\'m a module.  Don\'t run me directly!')
    sys.exit(-1)
