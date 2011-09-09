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

def process_book(iabook, ebook, alt_booktext=None):
    aby_ns="{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}"
    scandata = iabook.get_scandata()
    aby_file = iabook.get_abbyy()

    scandata_ns = iabook.get_scandata_ns()
    bookData = iabook.get_bookdata()

    # some books no scanlog
#     scanLog = scandata.find(scandata_ns + 'scanLog')
#     if scanLog is None:
#         scanLog = scandata.scanLog

    contents = iabook.get_toc()
    metadata = iabook.get_metadata()
    title = common.get_metadata_tag_data(metadata, 'title')
    if title is None:
        title = ''
    author = common.get_metadata_tag_data(metadata, 'creator')
    if author is None:
        author = ''

    ebook.push_tag('frontmatter')
    ebook.add_tag('doctitle', title)
    # ebook.add_tag('covertitle', title)
    ebook.add_tag('docauthor', author)

    ebook.push_navpoint('level', 'h', 'Producer\'s Note')
    ebook.push_navpoint('level', 'h', 'About Internet Archive Daisy Books')
    ebook.add_tag('p', """This book was produced in DAISY format by the Internet Archive.  The
    book pages were scanned and converted to DAISY format
    automatically.  This process relies on optical character
    recognition, and is somewhat susceptible to errors.  These errors
    may include weird characters, non-words, and incorrect guesses at
    structure.  Page numbers and headers or footers may remain from
    the scanned page.  The Internet Archive is working to improve the
    scanning process and resulting books, but in the meantime, we hope
    that this book will be useful to you.
    """)
    ebook.pop_navpoint()
    ebook.push_navpoint('level', 'h', 'About this DAISY book')
    has_nav = False
    if iabook.has_pagenos():
        has_nav = True
        ebook.add_tag('p', "This book has page navigation.")
    if contents is not None:
        has_nav = True
        ebook.add_tag('p', "This book has chapter navigation.")
    if not has_nav:
        ebook.add_tag('p', "This book as paragraph navigation, "
                      "but is otherwise unstructured.")
    ebook.pop_navpoint()
    ebook.push_navpoint('level', 'h', 'About the Internet Archive')
    ebook.add_tag('p', """The Internet Archive was founded in 1996
    to build an Internet library
and to promote universal access to all knowledge.  The Archive's purposes
include offering permanent access for researchers, historians,
scholars, people with disabilities, and the general public to
historical collections that exist in digital format.  The Internet Archive
includes texts, audio, moving images, and software as well as archived
web pages, and provides specialized services for information access
for the blind and other persons with disabilities.
    """)
    ebook.pop_navpoint()
    ebook.pop_navpoint()
    
    ebook.pop_tag()
    ebook.push_tag('bodymatter')

#     ebook.push_navpoint('level', 'h', 'Start of book')
#     pushed_navpoint = True

    if contents is None:
        ebook.push_navpoint('level', 'h', 'Book')

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
    for i, (event, page) in enumerate(context):
        # wrap in try/finally to ensure page.clear() is called
        try:
            if alt_booktext is not None:
                ebook.add_tag('p', alt_booktext)
                break

            page_scandata = iabook.get_page_scandata(i)
            pageno = None
            if page_scandata is not None:
                pageno = page_scandata.find(scandata_ns + 'pageNumber')
                if pageno:
                    pageno = pageno.text
            if pageno:
                if contents is not None and pageno in contents:
                    if pushed_navpoint:
                        ebook.pop_navpoint()
                    ebook.push_navpoint('level', 'h', contents[pageno])
                    pushed_navpoint = True
                part_str = 'part' + str(part_number).zfill(4)
                ebook.add_pagetarget(pageno, pageno)


            def include_page(page_scandata):
                if page_scandata is None:
                    return False
                add = page_scandata.find(scandata_ns + 'addToAccessFormats')
                if add is None:
                    add = page_scandata.addToAccessFormats
                if add is not None and add.text == 'true':
                    return True
                else:
                    return False

            if not include_page(page_scandata):
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
                                    # skip if its the first line and it could be a header
                                    if first_par and common.par_is_pageno_header_footer(par):
                                        saw_pageno_header_footer = True
                                        first_par = False
                                        continue
                                    first_par = False

                                    # skip if it's the last par and it could be a header
                                    if (not saw_pageno_header_footer
                                        and block == page[-1]
                                        and el == block[-1]
                                        and par == el[-1]
                                        and common.par_is_pageno_header_footer(par)):
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
        finally:
            page.clear()

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
