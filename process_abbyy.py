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

# remove me for faster execution
import os
debugme = os.environ.get('DEBUG')
if debugme:
    from  pydbgr.api import debug
else:
    def debug():
        pass

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
    md = objectify.parse(iabook.get_metadata()).getroot()
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
                result.append({ 'item':dc_ns+tagname, 'text':tag.text,
                                'atts':{ 'id':'bookid' } })
            elif tagname == 'language':
                # "use a RFC3066 language code"
                # try to translate to standard notation
                lang_map = {} # { 'eng':'en-US' }
                lang = (lang_map[md.language.text]
                        if md.language.text in lang_map
                        else md.language.text)
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
    scandata = objectify.parse(iabook.get_scandata()).getroot()
    metadata = objectify.parse(iabook.get_metadata()).getroot()
    aby_file = iabook.get_abbyy()

    bookData = scandata.find('bookData')
    scanLog = scandata.find('scanLog')
    scandata_pages = scandata.xpath('/book/pageData/page')

    paragraphs = []
    i = 0
    cover_number = 0
    nav_number = 0
    context = etree.iterparse(aby_file,
                              tag=aby_ns+'page',
                              resolve_entities=False)
    found_title = False
    for page_scandata in scandata_pages: #scan thru to make sure title exists
        if page_scandata.pageType.text == 'Title':
            found_title = True
            break
    # True if no title found, else False now, True later.
    before_title_page = found_title
    for event, page in context:
        page_scandata = scandata_pages[i]
        def include_page(page):
            add = page.find('addToAccessFormats')
            if add is not None and add.text == 'true':
                return True
            else:
                return False
        if not include_page(page_scandata):
            i += 1
            continue
        if page_scandata.pageType.text == 'Cover':
            (id, filename) = make_page_image(i, iabook, ebook)
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
            cover_number += 1
        elif page_scandata.pageType.text == 'Title':
            before_title_page = False
            (id, filename) = make_page_image(i, iabook, ebook)
            ebook.add_navpoint( { 'text':'Title Page', 'content':filename } )
            ebook.add_guide_item( { 'href':filename,
                                    'type':'title-page',
                                    'title':'Title Page' } )
        elif page_scandata.pageType.text == 'Copyright':
            (id, filename) = make_page_image(i, iabook, ebook)
            ebook.add_navpoint( { 'text':'Copyright', 'content':filename } )
            ebook.add_guide_item( { 'href':filename,
                                    'type':'copyright-page',
                                    'title':'Title Page' } )
        elif page_scandata.pageType.text == 'Contents':
            (id, filename) = make_page_image(i, iabook, ebook)
            ebook.add_navpoint( { 'text':'Contents', 'content':filename } )
            ebook.add_guide_item( { 'href':filename,
                                    'type':'toc',
                                    'title':'Title Page' } )
        elif page_scandata.pageType.text == 'Normal':
#             if i == 10:
#                 debug()
            if before_title_page:
                # XXX consider skipping if blank + no words?
                # make page image
                (id, filename) = make_page_image(i, iabook, ebook)
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

    tree = make_html('Archive',
                     [E.p('This book made available by the Internet Archive.')])
    ebook.add_content({ 'id':'intro',
                        'href':'intro.html',
                        'media-type':'application/xhtml+xml' },
                      common.tree_to_str(tree, xml_declaration=False))
    ebook.add_spine_item({ 'idref':'intro' })


    tree = make_html('sample title', paragraphs)
    ebook.add_content({ 'id':'book',
             'href':'book.html',
             'media-type':'application/xhtml+xml' },
                      common.tree_to_str(tree, xml_declaration=False))
    ebook.add_spine_item({ 'idref':'book' })
    ebook.add_navpoint({ 'text':'Book',
                         'content':'book.html' })
    ebook.add_guide_item( { 'href':'book.html',
                            'type':'text',
                            'title':'Book' } )

def make_page_image(i, iabook, ebook):
    image = iabook.get_image(i, width=600, height=780, quality=90)
    leaf_id = 'leaf' + str(i).zfill(4)
    ebook.add_content({ 'id':'leaf-image' + str(i).zfill(4),
                         'href':'images/' + leaf_id + '.jpg',
                         'media-type':'image/jpeg' },
                       image);
    img_tag = E.img({ 'src':'images/' + leaf_id + '.jpg',
                      'alt':'leaf ' + str(i) })
    tree = make_html('leaf ' + str(i).zfill(4), [ img_tag ])
    ebook.add_content({ 'id':leaf_id,
                        'href':leaf_id + '.html',
                        'media-type':'application/xhtml+xml' },
                      common.tree_to_str(tree, xml_declaration=False))
    ebook.add_spine_item({ 'idref':leaf_id, 'linear':'no' })

    return leaf_id, leaf_id + '.html'

def make_html(title, body_elems):
    html = E.html(
        E.head(
            E.title(title),
            E.meta(name='generator', content='abbyy to epub tool, v0.0'),
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
    sys.stderr.write('I''m a module.  Don''t run me directly!')
    sys.exit(-1)



# OPF
#manifest_items = [
#     { 'id' : 'ncx', 'href' : 'toc.ncx', 'media-type' : 'text/html' },
#     { 'id' : 'cover', 'href' : 'title.html', 'media-type' : 'application/xhtml+xml' },
#     { 'id' : 'content', 'href' : 'content.html', 'media-type' : 'application/xhtml+xml' },
#     { 'id' : 'cover-image', 'href' : 'images/cover.png', 'media-type' : 'image/png' },
#     { 'id' : 'css', 'href' : 'stylesheet.css', 'media-type' : 'text/css' },
# spine_items = [
#     { 'idref' : 'book' }
#     { 'idref' : 'cover', 'linear' : 'no' },
#     { 'idref' : 'content' }
# guide_items = [
#     { 'href' : 'title.html', 'type' : 'cover', 'title' : 'cover' }
# cover  	 the book cover(s), jacket information, etc.
# title-page 	page with possibly title, author, publisher, and other metadata
# toc 	table of contents
# index 	back-of-book style index
# glossary 	
# acknowledgements 	
# bibliography 	
# colophon 	
# copyright-page 	
# dedication 	
# epigraph 	
# foreword 	
# loi 	list of illustrations
# lot 	list of tables
# notes 	
# preface 	
# text 	First "real" page of content (e.g. "Chapter 1") 
#
# NCX navpoints = [
#     { 'id' : 'navpoint-1', 'playOrder' : '1', 'text' : 'Book', 'content' : 'book.html' },
#     { 'id' : 'navpoint-1', 'playOrder' : '1', 'text' : 'Book Cover', 'content' : 'title.html' },
#     { 'id' : 'navpoint-2', 'playOrder' : '2', 'text' : 'Contents', 'content' : 'content.html' },
# CAN NEST NAVPOINTS
