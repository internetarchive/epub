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

import epub

# remove me for faster execution
debugme = True
if debugme:
    from  pydbgr.api import debug
else:
    def debug():
        pass

# XXX need review of temp dir choice
# and translation of
# if (!file_exists('/tmp/stdout.ppm'))
# {
#   system('ln -s /dev/stdout /tmp/stdout.ppm');
# }
 
# get python string with image data - from .jp2 image in zip
def get_image(zipf, image_path, region, height, quality):
    output = os.popen('unzip -p ' + zipf + ' ' + image_path +
        ' | kdu_expand -region "' + region + '" ' +
           ' -no_seek -i /dev/stdin -o /tmp/stdout.ppm' +
        ' | pamscale -height ' + height +
        ' | pnmtojpeg -quality ' + quality)
    return output.read()

def get_meta_items(book_id):
    md = objectify.parse(book_id + '_meta.xml').getroot()
    dc_ns = '{http://purl.org/dc/elements/1.1/}'
    result = [{ 'item':'meta', 'atts':{ 'name':'cover', 'content':'cover-image' } }]
    result = [{ 'item':dc_ns+'type', 'text':'Text' }]
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
                # try to translate to standard notation
#                lang_map = { 'eng':'en-US' }
                lang_map = {}
                lang = lang_map[md.language.text] if md.language.text in lang_map else md.language.text
                result.append({ 'item':dc_ns+tagname, 'text':lang })
            elif tagname == 'type' and tag.text == 'Text':
                # already included above
                continue
            else:
                result.append({ 'item':dc_ns+tagname, 'text':tag.text })
    return result

aby_ns="{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}"
def generate_epub_items(book_id):
    scandata = objectify.parse(book_id + '_scandata.xml').getroot()
    metadata = objectify.parse(book_id + '_meta.xml').getroot()
    aby_file = gzip.open(book_id + '_abbyy.gz', 'rb')
    context = etree.iterparse(aby_file,  tag=aby_ns+'page', resolve_entities=False)

    bookData = scandata.find('bookData')
    scanLog = scandata.find('scanLog')
    scandata_pages = scandata.xpath('/book/pageData/page')
    paragraphs = []
    i = 0
    for event, page in context:
        page_data = scandata_pages(i)
        if not include_page(scandata_pages(i)):
            continue
        if page_data
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
                        lines = []
                        for line in par:
                            lines.append(etree.tostring(line, method='text', encoding=unicode))
                        paragraph.append(E.p(' '.join(lines)))
                   
                elif (el.tag == aby_ns+'row'):
                    pass
                else:
                    print('unexpected tag type' + el.tag)
                    sys.exit(-1)
        page.clear()
        i += 1

    tree = make_html('sample title', 'path_to_stylesheet', paragraphs)

    tree = build_html(context, scandata, metadata)
    yield ('content',
           { 'id':'book',
             'href':'book.html',
             'media-type':'application/xhtml+xml' },
           tree)
    yield ('spine', { 'idref':'book' }, None)
    yield ('navpoint',  { 'id':'navpoint-1',
                          'playOrder': '1',
                          'text':'Book',
                          'content':'book.html' }, None)
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

def include_page(page):
    add = page.find('addToAccessFormats')
    if add is not None and add.text == 'true':
        return True
    else:
        return False


def make_html(title, stylesheet_href, body_elems):
    from lxml.builder import E
    html = E.html(
        E.head(
            E.title(title),
            E.meta(name='generator', content='abbyy to epub tool'),
            E.link(rel='stylesheet',
                href=stylesheet_href,
                type='text/css'),
            E.meta({'http-equiv':'Content-Type',
                'content':'application/xhtml+xml; charset=utf-8'})
        ),
        E.body(
            E.div({ 'class':'body' })
        ),
        xmlns='http://www.w3.org/1999/xhtml'
    )
    html.xpath('/html/body/div')[0].append(body_elems)
    return etree.ElementTree(html)

