#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from lxml import etree
from lxml import objectify

import common
import zipfile
from datetime import datetime
import os
import sys
from StringIO import StringIO

from debug import debug, debugging

class Book(object):
    def __init__(self, out_name, metadata, content_dir='OEBPS/'):
        self.content_dir = content_dir
        self.dt = datetime.now()
        self.z = zipfile.ZipFile(out_name, 'w')
        self.add('mimetype', 'application/epub+zip', deflate=False)

        self.book_id = common.get_metadata_tag_data(metadata, 'identifier')
        self.title = common.get_metadata_tag_data(metadata, 'title')
        self.author = common.get_metadata_tag_data(metadata, 'creator')

        tree_str = make_container_info(content_dir)
        self.add('META-INF/container.xml', tree_str)

        (self.opf, self.opf_manifest_el,
         self.opf_spine_el, self.opf_guide_el) = make_opf(metadata)
        
        (self.ncx, self.ncx_head_el,
         self.ncx_navmap_el, self.ncx_pagelist_el) = make_ncx(self.book_id,
                                                              self.title,
                                                              self.author)

        self.tag_stack = []
        self.navpoint_stack = [self.ncx_navmap_el]
        self.id_index = 1
        self.nav_number = 1
        self.depth = 0
        self.current_depth = 0

        # Add static extra files - style sheet, etc.
        for id, href, media_type in [('css', 'stylesheet.css', 'text/css')]:
            content_src = os.path.join(sys.path[0], 'epub_files', href)
            content_str = open(content_src, 'r').read()
            self.add_content(id, href, media_type, content_str)


    def add_content(self, id, href, media_type, content_str):
        # info is e.g. { 'id':'title',
        #                'href':'title.html',
        #                'media-type':'application/xhtml+xml' },
        etree.SubElement(self.opf_manifest_el,
                         'item',
                         { 'id':id, 'href':href, 'media-type':media_type })
        self.add(self.content_dir + href, content_str)


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


    def push_navpoint(self, text):
        self.current_depth += 1
        if self.current_depth > self.depth:
            self.depth = self.current_depth
        navpoint_el = self.add_navpoint(text)
        self.navpoint_stack.append(navpoint_el)


    def pop_navpoint(self):
        self.current_depth -= 1
        return self.navpoint_stack.pop()


    def add_pagetarget(self, name, value, page_href, type='normal'):
        pagetarget_id = 'pagetarget' + str(self.id_index).zfill(6)
        self.id_index += 1
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
    for md in metadata:
        tagname = md['tag']
        if not tagname in [ 'title', 'creator', 'subject', 'description',
                           'publisher', 'contributor', 'date', 'type',
                           'format', 'identifier', 'source', 'language',
                           'relation','coverage', 'rights' ]:
            continue
        # XXX should make sure req'd is present somehow
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
    metas = [
        { 'name' : 'dtb:uid', 'content' : 'test id' },
        { 'name' : 'dtb:totalPageCount', 'content' : '0' },
        { 'name' : 'dtb:maxPageNumber', 'content' : '0' },
#         { 'name' : 'dtb:depth', 'content' : '1' },
        ]
    for item in metas:
        etree.SubElement(head_el, 'meta', item)
    doctitle = etree.SubElement(root_el, 'docTitle')
    etree.SubElement(doctitle, 'text').text = title;
    doctitle = etree.SubElement(root_el, 'docAuthor')
    etree.SubElement(doctitle, 'text').text = author;

    navmap_el = etree.SubElement(root_el, 'navMap')
    navinfo_el = etree.SubElement(navmap_el, 'navInfo')
    etree.SubElement(navinfo_el, 'text').text = 'Book navigation'

    pagelist_el = etree.SubElement(root_el, 'pageList')
    navlabel_el = etree.SubElement(pagelist_el, 'navLabel')
    etree.SubElement(navlabel_el, 'text').text = 'Pages'

    return tree, head_el, navmap_el, pagelist_el


if __name__ == '__main__':
    sys.stderr.write('I\'m a module.  Don\'t run me directly!')
    sys.exit(-1)
