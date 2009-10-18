#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import getopt
import re
import os
import gzip
import zipfile

try:
    from lxml import etree
except ImportError:
    sys.path.append('/petabox/sw/lib/lxml/lib/python2.5/site-packages') 
    from lxml import etree
from lxml import objectify
from lxml import html
import lxml
from lxml.builder import E

import common

import iarchive

from debug import debug, debugging, assert_d

def process_book(iabook, ebook):
    aby_ns="{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}"
    scandata = iabook.get_scandata()
    aby_file = iabook.get_abbyy()

    bookData = scandata.find('bookData')
    # XXX should fix below and similar by ensuring that scandata
    #   is always the same fmt...
    # scandata.zip/scandata.xml parses different?
    if bookData is None:
        bookData = scandata.bookData

    # some books no scanlog
#     scanLog = scandata.find('scanLog')
#     if scanLog is None:
#         scanLog = scandata.scanLog

    contents = iabook.get_toc()
    metadata = iabook.get_metadata()
    title = common.get_metadata_tag_data(metadata, 'title')
    author = common.get_metadata_tag_data(metadata, 'creator')

    ebook.push_tag('frontmatter')
    ebook.add_tag('doctitle', title)
    ebook.add_tag('covertitle', title)
    ebook.add_tag('docauthor', author)
    ebook.pop_tag()
    ebook.push_tag('bodymatter')

    if contents is None:
        ebook.push_navpoint('level', 'h', 'Book')

    i = 0
    part_number = 0
    cover_number = 0
    pushed_navpoint = False
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
            if contents is not None and str(pageno) in contents:
                if pushed_navpoint:
                    ebook.pop_navpoint()
                ebook.push_navpoint('level', 'h', contents[str(pageno)])
                pushed_navpoint = True
            part_str = 'part' + str(part_number).zfill(4)
            ebook.add_pagetarget(str(pageno), pageno)


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
                saw_pageno_header_footer = False

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
                                def par_is_pageno_header_footer(par):
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
                                        hdr_text = hdr_text.lower()
                                        rnums = ['i', 'ii', 'iii', 'iv',
                                                 'v', 'vi', 'vii', 'viii',
                                                 'ix', 'x', 'xi', 'xii',
                                                 'xiii', 'xiv', 'xv', 'xvi',
                                                 'xvii', 'xviii', 'xix', 'xx',
                                                 'xxi', 'xxii', 'xxiii', 'xxiv',
                                                 'xxv', 'xxvi', 'xxvii',
                                                 'xxviii', 'xxix', 'xxx',
                                                 ]
                                        if hdr_text in rnums:
                                            return True
                                        # common OCR errors
                                        if re.match('[0-9afhiklmnouvx^]+',
                                                    hdr_text):
                                            return True
                                    return False

                                # skip if its the first line and it could be a header
                                if first_par and par_is_pageno_header_footer(par):
                                    saw_pageno_header_footer = True
                                    first_par = False
                                    continue
                                first_par = False

                                # skip if it's the last par and it could be a header
                                if (not saw_pageno_header_footer
                                    and block == page[-1]
                                    and el == block[-1]
                                    and par == el[-1]
                                    and par_is_pageno_header_footer(par)):
                                    saw_pageno_header_footer = True
                                    continue
                                        
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
                                ebook.add_tag('p', ''.join(lines))
                        elif (el.tag == aby_ns+'row'):
                            pass
                        else:
                            print('unexpected tag type' + el.tag)
                            sys.exit(-1)

        page.clear()
        i += 1

    if pushed_navpoint:
        ebook.pop_navpoint()

    if contents is None:
        ebook.pop_navpoint() #level1

    ebook.pop_tag()
    ebook.push_tag('rearmatter')
    ebook.push_tag('level1')
    ebook.add_tag('p', 'End of book')
    ebook.pop_tag()
    ebook.pop_tag()

if __name__ == '__main__':
    sys.stderr.write('I\'m a module.  Don\'t run me directly!')
    sys.exit(-1)
