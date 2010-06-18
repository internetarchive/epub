#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from lxml import etree
from lxml import objectify
from lxml.builder import E

import common
import zipfile
from datetime import datetime
import os
import sys
from StringIO import StringIO
import base64

from debug import debug, debugging, assert_d

class Book(object):
    def __init__(self, out_name, metadata, content_dir='OEBPS/'):
        self.content_dir = content_dir
        self.dt = datetime.now()
        self.z = zipfile.ZipFile(out_name, 'w')
        self.add('mimetype', 'application/epub+zip', deflate=False)

        self.book_id = common.get_metadata_tag_data(metadata, 'identifier')
        self.title = common.get_metadata_tag_data(metadata, 'title')
        if self.title is None:
            self.title = 'none'
        self.author = common.get_metadata_tag_data(metadata, 'creator')
        if self.author is None:
            self.author = 'none'

        tree_str = make_container_info(content_dir)
        self.add('META-INF/container.xml', tree_str)

        (self.opf, self.opf_manifest_el,
         self.opf_spine_el, self.opf_guide_el) = make_opf(metadata)
        
        (self.ncx, self.ncx_head_el,
         self.ncx_navmap_el) = make_ncx(self.book_id,
                                        self.title,
                                        self.author)
        self.ncx_pagelist_el = None

        self.navpoint_stack = [self.ncx_navmap_el]
        self.id_index = 1
        self.nav_number = 1
        self.depth = 0
        self.current_depth = 0

        self.el_stack = []
        self.el_len_total = 0
        self.max_el_len_total = 150000
        self.part_number = 0
        self.current_part = None

        # Add static extra files - style sheet, etc.
        for id, href, media_type in [('css', 'stylesheet.css', 'text/css')]:
            content_src = os.path.join(sys.path[0], 'epub_files', href)
            content_str = open(content_src, 'r').read()
            self.add_content(id, href, media_type, content_str)


    def flush_els(self):
        if self.current_part is None:
            return
        part_str = 'part' + str(self.part_number).zfill(4)
        part_str_href = part_str + '.html'
        self.add_content(part_str, part_str_href, 'application/xhtml+xml',
                         common.tree_to_str(self.current_part, xml_declaration=False))
        self.add_spine_item({ 'idref':part_str })
        if self.part_number == 0:
            self.add_guide_item({ 'href':part_str_href,
                                   'type':'text',
                                   'title':'Book' })
        self.part_number += 1
        self.el_stack = [] # xxx ? require popped?
        self.el_len_total = 0
        self.current_part = None


    def add_el(self, el, el_len=100):
        if self.el_len_total > self.max_el_len_total:
            self.flush_els()
        if len(self.el_stack) == 0:
            assert_d(self.current_part == None)
            self.current_part, body_el = self.make_xhtml()
            self.el_stack.append(body_el)
        self.el_stack[-1].append(el)
        self.el_len_total += el_len
        return 'part' + str(self.part_number).zfill(4) + '.html'


    def push_el(self, el, el_len):
        result = self.add_el(el)
        self.el_stack.append(el)
        return result
    

    def pop_el(self):
        self.el_stack.pop()

    def make_xhtml(self):
        html = E.html(
            E.head(
                E.title('part' + str(self.part_number).zfill(4)),
                E.meta(name='generator', content='abbyy to epub tool, v0.2'),
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
        return etree.ElementTree(html), html.xpath('/html/body/div')[0]


    def add_content(self, id, href, media_type, content_str, deflate=True):
        # info is e.g. { 'id':'title',
        #                'href':'title.html',
        #                'media-type':'application/xhtml+xml' },
        etree.SubElement(self.opf_manifest_el,
                         'item',
                         { 'id':id, 'href':href, 'media-type':media_type })
        self.add(self.content_dir + href, content_str, deflate)


    def add_spine_item(self, info):
        # info is e.g. { 'idref':'title' }
        # ... or { 'idref':'copyright', 'linear':'no' }
        etree.SubElement(self.opf_spine_el, 'itemref', info)


    def add_guide_item(self, info):
        etree.SubElement(self.opf_guide_el, 'reference', info)


    def add_navpoint(self, text, href):
        level = str(len(self.navpoint_stack))
        current_navpoint_el = self.navpoint_stack[-1]
        navpoint_id = 'navpoint' + str(self.id_index).zfill(6)
        self.id_index += 1
        navpoint_el = etree.SubElement(current_navpoint_el, 'navPoint',
                                       { 'id':'navpoint' + navpoint_id,
                                         'class':'navpoint-level' + level,
                                         'playOrder':str(self.nav_number) })
        navlabel_el = etree.SubElement(navpoint_el, 'navLabel')
        etree.SubElement(navlabel_el, 'text').text = text
        etree.SubElement(navpoint_el, 'content',
                         { 'src':href })
        self.nav_number += 1
        return navpoint_el


    def push_navpoint(self, text, href):
        self.current_depth += 1
        if self.current_depth > self.depth:
            self.depth = self.current_depth
        navpoint_el = self.add_navpoint(text, href)
        self.navpoint_stack.append(navpoint_el)


    def pop_navpoint(self):
        self.current_depth -= 1
        return self.navpoint_stack.pop()


    def add_pagetarget(self, name, value, page_href, type='normal'):
        pagetarget_id = 'pagetarget' + str(self.id_index).zfill(6)
        self.id_index += 1
        
        if self.ncx_pagelist_el is None:
            self.ncx_pagelist_el = make_pagelist_el(self.ncx)
        
        pagetarget_el = etree.SubElement(self.ncx_pagelist_el,
                                         'pageTarget',
                                         { 'id':pagetarget_id,
                                           'value':str(value),
                                           'type':type,
                                           'playOrder':str(self.nav_number) })
        navlabel_el = etree.SubElement(pagetarget_el, 'navLabel')
        etree.SubElement(navlabel_el, 'text').text = name
        etree.SubElement(pagetarget_el, 'content',
                         { 'src':page_href })
        self.nav_number += 1


    def add(self, path, content_str, deflate=True):
        info = zipfile.ZipInfo(path)
        info.compress_type = (zipfile.ZIP_DEFLATED if deflate
                              else zipfile.ZIP_STORED)
        info.external_attr = 0666 << 16L # fix access
        info.date_time = (self.dt.year, self.dt.month, self.dt.day,
                          self.dt.hour, self.dt.minute, self.dt.second)
        self.z.writestr(info, content_str)


    def finish(self, metadata):
        # ... Any remaining html?

        tree_str = common.tree_to_str(self.ncx)
        self.add_content('ncx', 'toc.ncx', 'application/x-dtbncx+xml',
                         tree_str)

        tree_str = common.tree_to_str(self.opf)
        self.add(self.content_dir + 'content.opf', tree_str)

        self.z.close()


def make_container_info(content_dir):
    root = etree.Element('container',
                     version='1.0',
                     xmlns='urn:oasis:names:tc:opendocument:xmlns:container')
    rootfiles = etree.SubElement(root, 'rootfiles')
    etree.SubElement(rootfiles, 'rootfile',
                     { 'full-path' : content_dir + 'content.opf',
                       'media-type' : 'application/oebps-package+xml' } )
    return common.tree_to_str(root)


def make_opf(metadata):
    xml = """<?xml version='1.0' encoding='utf-8'?>
<package xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="bookid"/>
"""
    tree = etree.parse(StringIO(xml))
    root_el = tree.getroot()

    dc = 'http://purl.org/dc/elements/1.1/'
    dcb = '{' + dc + '}'
    metadata_el = etree.SubElement(root_el, 'metadata')
    etree.SubElement(metadata_el, 'meta',
                     { 'name':'cover', 'content':'cover-image' })
    etree.SubElement(metadata_el, dcb+'type').text = 'Text'

    # Fill in missing required metadata fields with made-up entries
    md_tags = [ datum['tag'] for datum in metadata ]
    replacements = ( ('title', 'Unknown Title'),
                     ('language', 'eng'),
                     ('identifier', 'no_identifier'
                      + base64.b64encode(os.urandom(10))[:10]) )
    for k, v in replacements:
        if not k in md_tags:
            metadata.append({ 'tag': k, 'text': v })
    
    for md in metadata:
        tagname = md['tag']
        if not tagname in ( 'title', 'creator', 'subject', 'description',
                           'publisher', 'contributor', 'date', 'type',
                           'format', 'identifier', 'source', 'language',
                           'relation','coverage', 'rights' ):
            continue
        if tagname == 'identifier':
            el = etree.SubElement(metadata_el, dcb + tagname,
                                  { 'id':'bookid' })
        else:
            el = etree.SubElement(metadata_el, dcb + tagname)
        el.text = md['text']
    manifest_el = etree.SubElement(root_el, 'manifest')
    spine_el = etree.SubElement(root_el, 'spine', { 'toc':'ncx' })
    guide_el = etree.SubElement(root_el, 'guide')

    return tree, manifest_el, spine_el, guide_el


def make_ncx(book_id, title, author):
    xml = """<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"/>
"""
    tree = etree.parse(StringIO(xml))
    root_el = tree.getroot()
    head_el = etree.SubElement(root_el, 'head')
    metas = (
        { 'name' : 'dtb:uid', 'content' : 'test id' },
        { 'name' : 'dtb:totalPageCount', 'content' : '0' },
        { 'name' : 'dtb:maxPageNumber', 'content' : '0' },
#         { 'name' : 'dtb:depth', 'content' : '1' },
        )
    for item in metas:
        etree.SubElement(head_el, 'meta', item)
    doctitle = etree.SubElement(root_el, 'docTitle')
    etree.SubElement(doctitle, 'text').text = title;
    doctitle = etree.SubElement(root_el, 'docAuthor')
    etree.SubElement(doctitle, 'text').text = author;

    navmap_el = etree.SubElement(root_el, 'navMap')
    navinfo_el = etree.SubElement(navmap_el, 'navInfo')
    etree.SubElement(navinfo_el, 'text').text = 'Book navigation'

    # defer pagelist_el, as some books lack pages

    return tree, head_el, navmap_el

def make_pagelist_el(ncx):
    root_el = ncx.getroot()
    pagelist_el = etree.SubElement(root_el, 'pageList')
    navlabel_el = etree.SubElement(pagelist_el, 'navLabel')
    etree.SubElement(navlabel_el, 'text').text = 'Pages'
    return pagelist_el

if __name__ == '__main__':
    sys.stderr.write('I\'m a module.  Don\'t run me directly!')
    sys.exit(-1)
