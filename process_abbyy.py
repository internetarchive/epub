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
# 'some have optional attributes'
#     *  creator, contributor
#           o opf:role — see http://www.loc.gov/marc/relators/ for values
#     * date
#           o opf:event — unstandardised: use something sensible
#     * identifier
#           o opf:scheme — unstandardised: use something sensible
#     * date, format, identifier, language, type
#           o xsi:type — use an appropriate standard term
#               (such as W3CDTF for date)
#     * contributor, coverage, creator, description, publisher, relation,
#       rights, source, subject, title
#           o xml:lang — use RFC-3066 format
def get_meta_items(iabook):
    md = objectify.parse(iabook.get_metadata_path()).getroot()
    dc_ns = '{http://purl.org/dc/elements/1.1/}'
    result = [{ 'item':'meta', 'atts':{ 'name':'cover',
                                        'content':'cover-image1' } },
              { 'item':dc_ns+'type', 'text':'Text' }]
    # catch dublin core stragglers
    for tagname in [ 'title', 'creator', 'subject', 'description',
                     'publisher', 'contributor', 'date', 'type',
                     'format', 'identifier', 'source', 'language',
                     'relation','coverage', 'rights' ]:
        for tag in md.findall(tagname):
            if tagname == 'identifier':
                from datetime import datetime
                dt = datetime.now()
                xtra = (str(dt.year) + str(dt.month) + str(dt.day) +
                        str(dt.hour) + str(dt.minute) + str(dt.second))
                result.append({ 'item':dc_ns+tagname, 'text':tag.text + xtra,
                                'atts':{ 'id':'bookid' } })
            elif tagname == 'language':
                # "use a RFC3066 language code"
                # try to translate to standard notation
                lang = iarchive.iso_639_23_to_iso_639_1(md.language.text)
                result.append({ 'item':dc_ns+tagname, 'text':lang })
            elif tagname == 'type' and tag.text == 'Text':
                # already included above
                continue
#             elif tagname == 'date':
#                 dc:date xsi:type="dcterms:W3CDTF">2007-12-28</dc:date>
            else:
                result.append({ 'item':dc_ns+tagname, 'text':tag.text })
    return result

def process_book(iabook, ebook):
    aby_ns="{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}"
    scandata = iabook.get_scandata()
    metadata = objectify.parse(iabook.get_metadata_path()).getroot()
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

    paragraphs = []
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
            paragraphs.append(pdiv)
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
            (id, filename) = make_html_page_image(i, iabook, ebook)
            if cover_number == 0:
                cover_title = 'Front Cover'
            else:
                cover_title = 'Back Cover' ## xxx detect back page?
            ebook.add_navpoint( { 'text':cover_title, 'content':filename } )
            if cover_number == 0:
                ebook.add_guide_item( { 'href':filename,
                                        'type':'cover',
                                        'title':cover_title } )
                ebook.add_cover_id(id)

                # Add intro page after 1rst cover page
                tree = make_html('Archive',
                     [E.p('This book made available by the Internet Archive.')])
                ebook.add_content({ 'id':'intro',
                                    'href':'intro.html',
                                    'media-type':'application/xhtml+xml' },
                                  common.tree_to_str(tree,
                                                     xml_declaration=False))
                ebook.add_spine_item({ 'idref':'intro', 'linear':'no' })
            cover_number += 1

        elif page_type == 'title' or page_type == 'title page':
            before_title_page = False
            (id, filename) = make_html_page_image(i, iabook, ebook)
            ebook.add_navpoint( { 'text':'Title Page', 'content':filename } )
            ebook.add_guide_item( { 'href':filename,
                                    'type':'title-page',
                                    'title':'Title Page' } )
        elif page_type == 'copyright':
            (id, filename) = make_html_page_image(i, iabook, ebook)
            ebook.add_navpoint( { 'text':'Copyright', 'content':filename } )
            ebook.add_guide_item( { 'href':filename,
                                    'type':'copyright-page',
                                    'title':'Title Page' } )
        elif page_type == 'contents':
            (id, filename) = make_html_page_image(i, iabook, ebook)
            ebook.add_navpoint( { 'text':'Contents', 'content':filename } )
            ebook.add_guide_item( { 'href':filename,
                                    'type':'toc',
                                    'title':'Title Page' } )
        elif page_type == 'normal':
#             if i == 10:
#                 debug()
            if before_title_page:
                # XXX consider skipping if blank + no words?
                # make page image
                (id, filename) = make_html_page_image(i, iabook, ebook)
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
                                paragraphs.append(E.p(''.join(lines)))
                        elif (el.tag == aby_ns+'row'):
                            pass
                        else:
                            print('unexpected tag type' + el.tag)
                            sys.exit(-1)

        page.clear()
        i += 1

        if len(paragraphs) > 100:
            # make a chunk!
            part_str = 'part' + str(part_number).zfill(4)
            part_str_href = part_str + '.html'
            tree = make_html('sample title', paragraphs)
            ebook.add_content({ 'id':part_str,
                                'href':part_str_href,
                                'media-type':'application/xhtml+xml' },
                              common.tree_to_str(tree, xml_declaration=False))
            ebook.add_spine_item({ 'idref':part_str })
            if part_number == 0:
                ebook.add_guide_item( { 'href':part_str_href,
                                        'type':'text',
                                        'title':'Book' } )
                ebook.add_navpoint({ 'text':'Pages',
                                     'content':part_str_href })
            part_number += 1
            paragraphs = []
    # make chunk from last paragraphs
    if len(paragraphs) > 100:
        part_str = 'part' + str(part_number).zfill(4)
        part_str_href = part_str + '.html'
        tree = make_html('Book part ' + str(part_number), paragraphs)
        ebook.add_content({ 'id':part_str,
                            'href':part_str_href,
                            'media-type':'application/xhtml+xml' },
                          common.tree_to_str(tree, xml_declaration=False))
        ebook.add_spine_item({ 'idref':part_str })
        if part_number == 0:
            book.add_guide_item( { 'href':part_str_href,
                                    'type':'text',
                                    'title':'Book' } )
            ebook.add_navpoint({ 'text':'Pages',
                                 'content':part_str_href })

def make_html_page_image(i, iabook, ebook):
    image = iabook.get_page_image(i, width=600, height=800, quality=90)
    leaf_id = 'leaf' + str(i).zfill(4)
    leaf_image_id = 'leaf-image' + str(i).zfill(4)
    ebook.add_content({ 'id':leaf_image_id,
                         'href':'images/' + leaf_image_id + '.jpg',
                         'media-type':'image/jpeg' },
                       image);
    img_tag = E.img({ 'src':'images/' + leaf_image_id + '.jpg',
                      'alt':'leaf ' + str(i) })
    tree = make_html('leaf ' + str(i).zfill(4), [ img_tag ])
    ebook.add_content({ 'id':leaf_id,
                        'href':leaf_id + '.html',
                        'media-type':'application/xhtml+xml' },
                      common.tree_to_str(tree, xml_declaration=False))
    ebook.add_spine_item({ 'idref':leaf_id, 'linear':'no' })

    return leaf_id, leaf_id + '.html'

def make_page_image(i, iabook, ebook):
    image = iabook.get_image(i, width=600, height=800, quality=90)
    leaf_image_id = 'leaf-image' + str(i).zfill(4)
    ebook.add_content({ 'id':leaf_image_id,
                         'href':'images/' + leaf_image_id + '.jpg',
                         'media-type':'image/jpeg' },
                       image);
    ebook.add_spine_item({ 'idref':leaf_image_id, 'linear':'no' })
    return leaf_image_id, 'images/' + leaf_image_id + '.jpg'

def make_html(title, body_elems):
    html = E.html(
        E.head(
            E.title(title),
            E.meta(name='generator', content='abbyy to epub tool, v0.1'),
            E.link(rel='stylesheet',
                   href='stylesheet.css',
                   type='text/css'),
#             E.link(rel='stylesheet',
#                    href='page-template.xpgt',
#                    type='application/vnd.adobe-page-template+xml'),
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
