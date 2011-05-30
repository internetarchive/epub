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


max_width = 600
max_height = 780

def process_book(iabook, ebook):
    aby_ns="{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}"
    scandata = iabook.get_scandata()

    scandata_ns = iabook.get_scandata_ns()
    bookData = iabook.get_bookdata()
    
    aby_file = iabook.get_abbyy()

    # some books no scanlog
#     scanLog = scandata.find(scandata_ns + 'scanLog')
#     if scanLog is None:
#         scanLog = scandata.scanLog

    contents = iabook.get_toc()
    metadata = iabook.get_metadata()
    title = common.get_metadata_tag_data(metadata, 'title')
    if title is None:
        title = 'none'
    author = common.get_metadata_tag_data(metadata, 'creator')
    if author is None:
        author = 'none'

    i = 0
    cover_number = 0
    toc_item_number = 0
    picture_number = 0
    pushed_chapters = False
    made_contents_navpoint = False
    made_pages = False
    context = etree.iterparse(aby_file,
                              tag=aby_ns+'page',
                              resolve_entities=False)
    found_title = False
    for page_scandata in iabook.get_scandata_pages(): #confirm title exists
        try:
            t = page_scandata.pageType.text.lower()
        except AttributeError:
            t = 'normal'

        if t == 'title' or t == 'title page':
            found_title = True
            break
    # True if no title found, else False now, True later.
    before_title_page = found_title
    for event, page in context:
        page_scandata = iabook.get_page_scandata(i)
        pageno = None
        if page_scandata is not None:
            pageno = page_scandata.find(scandata_ns + 'pageNumber')
        if pageno:
            if contents is not None and str(pageno) in contents:
                ebook.flush_els()
                if not pushed_chapters:
                    cdiv = E.div({ 'class':'newnav', 'id':'chapters' })
                    href = ebook.add_el(cdiv) + '#' + 'chapters'
                    ebook.push_navpoint('Chapters', href)
                    pushed_chapters = True
                id = 'toc-' + str(toc_item_number)
                toc_item_number += 1
                cdiv = E.div({ 'class':'newnav', 'id':id })
                href = ebook.add_el(cdiv) + '#' + id
                ebook.add_navpoint(contents[str(pageno)], href)

            id = 'page-' + str(pageno)
            pdiv = E.div({ 'class':'newpage', 'id':id })
            href = ebook.add_el(pdiv) + '#' + id
            ebook.add_pagetarget(str(pageno), pageno, href)

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
            i += 1
            continue

        try:
            page_type = page_scandata.pageType.text.lower()
        except AttributeError:
            page_type = 'normal'

        if page_type == 'cover':
            if cover_number == 0:
                cover_title = 'Front Cover'
                front_cover = True
            else:
                cover_title = 'Back Cover' ## xxx detect back page?
                front_cover = False
                ebook.flush_els()
                if pushed_chapters:
                    ebook.pop_navpoint()
                    pushed_chapters = False
            
            (id, filename) = make_html_page_image(i, iabook, ebook,
                                                  cover=front_cover)
            if id is not None:
                ebook.add_navpoint(cover_title, filename)
                if cover_number == 0:
                    ebook.add_guide_item({ 'href':filename,
                                           'type':'cover',
                                           'title':cover_title })

                    # Add intro page after 1rst cover page
                    tree = make_html('Archive',
                         [E.p('This book made available by the Internet Archive.')])
                    ebook.add_content('intro', 'intro.html',
                                      'application/xhtml+xml',
                                      common.tree_to_str(tree,
                                                         xml_declaration=False))
                    ebook.add_spine_item({ 'idref':'intro', 'linear':'no' })
                cover_number += 1

        elif page_type == 'title' or page_type == 'title page':
            before_title_page = False
            (id, filename) = make_html_page_image(i, iabook, ebook)
            if id is not None:
                ebook.add_navpoint('Title Page', filename)
                ebook.add_guide_item({ 'href':filename,
                                       'type':'title-page',
                                       'title':'Title Page' })
        elif page_type == 'copyright':
            (id, filename) = make_html_page_image(i, iabook, ebook)
            if id is not None:
                ebook.add_navpoint('Copyright', filename)
                ebook.add_guide_item({ 'href':filename,
                                       'type':'copyright-page',
                                       'title':'Title Page' })
        elif page_type == 'contents':
            (id, filename) = make_html_page_image(i, iabook, ebook)
            if id is not None:
                if not made_contents_navpoint:
                    ebook.add_navpoint('Table of Contents', filename)
                    made_contents_navpoint = True
                ebook.add_guide_item({ 'href':filename,
                                       'type':'toc',
                                       'title':'Title Page' })

        elif page_type == 'normal':
            if before_title_page:
                page_text = etree.tostring(page,
                                           method='text',
                                           encoding=unicode)
                # Skip if not much text
                if len(page_text) >= 10:
                    (id, filename) = make_html_page_image(i, iabook, ebook)
                # XXX note that above might return None, None and do nothing...
            else:
                first_par = True
                saw_pageno_header_footer = False
                
                for block in page:
                    if block.get('blockType') == 'Picture':
                        region = ((int(block.get('l')),
                                   int(block.get('t'))),
                                  (int(block.get('r')),
                                   int(block.get('b'))))
                        (l, t), (r, b) = region
                        region_width = r - l
                        region_height = b - t
                        orig_page_size = (int(page.get('width')),
                                     int(page.get('height')))
                        page_width, page_height = orig_page_size
                        
                        # XXX bad aspect ratio!
                        # XXX need fixed code to get requested size
                        req_width = int(max_width *
                                        (region_width / float(page_width)))
                        req_height = int(max_height *
                                         (region_height / float(page_height)))
                        image = iabook.get_page_image(i,
                                                      (req_width, req_height),
                                                      orig_page_size,
                                                      kdu_reduce=2,
                                                      region=region)
                        if image is not None:
                            pic_id = 'picture' + str(picture_number)
                            pic_href = 'images/' + pic_id + '.jpg'
                            picture_number += 1
                            ebook.add_content(pic_id, pic_href,
                                              'image/jpeg', image, deflate=False)
                            el = E.p({ 'class':'illus' },
                                     E.img(src=pic_href,
                                           alt=pic_id))
                            ebook.add_el(el)
                        continue
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

                                if not made_pages:
                                    made_pages = True
                                    if not contents:
                                        href = ebook.add_el(E.div({ 'class':'pages', 'id':'pages' }))
                                        ebook.add_navpoint('Pages', href)
                                to_add = ''.join(lines)
                                ebook.add_el(E.p(to_add), len(to_add))
                        elif (el.tag == aby_ns+'row'):
                            pass
                        else:
                            print('unexpected tag type' + el.tag)
                            sys.exit(-1)

        page.clear()
        i += 1

    ebook.flush_els()
    if pushed_chapters:
        ebook.pop_navpoint()



def make_html_page_image(i, iabook, ebook, cover=False):
    ebook.flush_els()
    image = iabook.get_page_image(i, (max_width, max_height))
    if image is None:
        return None, None
    leaf_id = 'leaf' + str(i).zfill(4)
    if not cover:
        leaf_image_id = 'leaf-image' + str(i).zfill(4)
    else:
        leaf_image_id = 'cover-image'
    ebook.add_content(leaf_image_id, 'images/' + leaf_image_id + '.jpg',
                      'image/jpeg', image, deflate=False)
    img_tag = E.img({ 'src':'images/' + leaf_image_id + '.jpg',
                      'alt':'leaf ' + str(i) })
    tree = make_html('leaf ' + str(i).zfill(4), [ img_tag ])
    ebook.add_content(leaf_id, leaf_id + '.html', 'application/xhtml+xml',
                      common.tree_to_str(tree, xml_declaration=False))
    ebook.add_spine_item({ 'idref':leaf_id, 'linear':'no' })
    return leaf_id, leaf_id + '.html'


def make_html(title, body_elems):
    html = E.html(
        E.head(
            E.title(title),
            E.meta(name='generator', content='abbyy to epub tool, v0.1'),
            E.link(rel='stylesheet',
                   href='stylesheet.css',
                   type='text/css'),
            E.meta({'http-equiv':'Content-Type',
                'content':'application/xhtml+xml; charset=utf-8'})
        ),
        E.body(
            E.div({ 'class':'body' })
        ),
        xmlns='http://www.w3.org/1999/xhtml'
    )
    for el in body_elems:
        html.xpath('/html/body/div')[0].append(el)
    return etree.ElementTree(html)


if __name__ == '__main__':
    sys.stderr.write('I\'m a module.  Don\'t run me directly!')
    sys.exit(-1)
