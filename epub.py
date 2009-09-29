#!/usr/bin/python
# -*- coding: utf-8 -*-

from lxml import etree
from lxml import objectify

import common
import zipfile
from datetime import datetime

from debug import debug, debugging

class Book(object):
    def __init__(self, epub_out, content_dir='OEBPS/'):
        self.dt = datetime.now()
        self.z = zipfile.ZipFile(epub_out, 'w')
        self.add('mimetype', 'application/epub+zip', deflate=False)
        self.content_dir = content_dir
        tree_str = make_container_info(content_dir)
        self.add('META-INF/container.xml', tree_str)

        # style sheet
        self.add(self.content_dir + 'stylesheet.css', make_stylesheet())

        # This file enables Adobe Digital Editions features,
        # if referenced by a content file.
        #
        # Source:
        # http://www.adobe.com/devnet/digitalpublishing/epubs/EPUBBestPractices-1_0_3.epub
        # ... link from
        # http://www.adobe.com/devnet/digitalpublishing/
        #self.add(self.content_dir + 'page-template.xpgt', make_ade_stylesheet())

        self.manifest_items = [
            { 'id':'ncx',
              'href':'toc.ncx',
              'media-type':'application/x-dtbncx+xml'
              },
            { 'id':'css',
              'href':'stylesheet.css',
              'media-type':'text/css'
              },
            ]
        self.spine_items = []
        self.guide_items = []
        self.navpoints = []
        self.cover_id = None

    def add_content(self, info, content):
        # info is e.g. { 'id':'title',
        #                'href':'title.html',
        #                'media-type':'application/xhtml+xml' },
        self.manifest_items.append(info)
        self.add(self.content_dir + ''+info['href'], content)

    def add_cover_id(self, cover_id):
        # used for meta tag to flag
        self.cover_id = cover_id

    def add_spine_item(self, info):
        # info is e.g. { 'idref':'title' }
        # ... or { 'idref':'copyright', 'linear':'no' }
        self.spine_items.append(info)

    def add_guide_item(self, info):
        # info is e.g. { 'href':'title.html',
        #                'type':'title-page',
        #                'title':'Title Page' }
        self.guide_items.append(info)

    def add_navpoint(self, info):
        # info is e.g. { 'text':'Title Page',
        #                'content':'title.html' }
        # navpoints added thru this interface are sequential -
        # id and playOrder are generated.
        self.navpoints.append(info)

    def add(self, path, content_str, deflate=True):
        info = zipfile.ZipInfo(path)
        info.compress_type = (zipfile.ZIP_DEFLATED if deflate
                              else zipfile.ZIP_STORED)
        info.external_attr = 0666 << 16L # fix access
        info.date_time = (self.dt.year, self.dt.month, self.dt.day,
                          self.dt.hour, self.dt.minute, self.dt.second)
        self.z.writestr(info, content_str)

    def finish(self, meta_info_items):
        tree_str = make_opf(meta_info_items,
                            self.manifest_items,
                            self.spine_items,
                            self.guide_items,
                            self.cover_id)
        self.add(self.content_dir + 'content.opf', tree_str)

        tree_str = make_ncx(self.navpoints)
        self.add(self.content_dir + 'toc.ncx', tree_str)

        self.z.close()

def make_container_info(content_dir='OEBPS/'):
    root = etree.Element('container',
                     version='1.0',
                     xmlns='urn:oasis:names:tc:opendocument:xmlns:container')
    rootfiles = etree.SubElement(root, 'rootfiles')
    etree.SubElement(rootfiles, 'rootfile',
                     { 'full-path' : content_dir + 'content.opf',
                       'media-type' : 'application/oebps-package+xml' } )
    return common.tree_to_str(root)

dc = 'http://purl.org/dc/elements/1.1/'
dcb = '{' + dc + '}'
def make_opf(meta_info_items,
             manifest_items,
             spine_items,
             guide_items,
             cover_id=None):
    root = etree.Element('package',
                         { 'xmlns' : 'http://www.idpf.org/2007/opf',
                           'unique-identifier' : 'bookid',
                           'version' : '2.0' },
                         nsmap={'dc' : dc })
    metadata = etree.SubElement(root, 'metadata')
    for item in meta_info_items:
        el = etree.SubElement(metadata, item['item'], item['atts']
                              if 'atts' in item
                              else None)
        if 'text' in item:
            el.text = item['text']
    manifest = etree.SubElement(root, 'manifest')
    for item in manifest_items:
        etree.SubElement(manifest, 'item', item)
#     if cover_id is not None:
#         etree.SubElement(manifest, 'meta', name='cover',
#                          content=cover_id)
    if len(spine_items) > 0:    
        spine = etree.SubElement(root, 'spine', toc='ncx')
    for item in spine_items:
        etree.SubElement(spine, 'itemref', item)
    if len(guide_items) > 0:
        guide = etree.SubElement(root, 'guide')
    for item in guide_items:
        etree.SubElement(guide, 'reference', item)
    return common.tree_to_str(root)

navpoints = [
    { 'id':'navpoint-1', 'playOrder':'1',
      'text':'Book', 'content':'book.html' },
    ]
def make_ncx(navpoints):
    import StringIO
    xml = """<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"/>
"""
    tree = etree.parse(StringIO.StringIO(xml))
    root = tree.getroot()
    head = etree.SubElement(root, 'head')
    metas = [
        { 'name' : 'dtb:uid', 'content' : 'test id' },
        { 'name' : 'dtb:depth', 'content' : '1' },
        { 'name' : 'dtb:totalPageCount', 'content' : '0' },
        { 'name' : 'dtb:maxPageNumber', 'content' : '0' },
        ]
    for item in metas:
        etree.SubElement(head, 'meta', item)
    doctitle = etree.SubElement(root, 'docTitle')
    etree.SubElement(doctitle, 'text').text = 'Hello World';
    navmap = etree.SubElement(root, 'navMap')
    nav_number = 0
    for item in navpoints:
        navpoint = etree.SubElement(navmap, 'navPoint',
                                    id=('navpoint' + str(nav_number)),
                                    playOrder=str(nav_number))
        navlabel = etree.SubElement(navpoint, 'navLabel')
        etree.SubElement(navlabel, 'text').text = item['text']
        etree.SubElement(navpoint, 'content', src=item['content'])
        nav_number = nav_number + 1
    tree = etree.ElementTree(root)
    return common.tree_to_str(tree)

def make_stylesheet():
    return '''body {
    font-family: serif;
}
h1,h2,h3,h4 {
    font-family: serif;
    color: red;
}
'''

def make_ade_stylesheet():
    # to be called 'page-template.xpgt'
    return '''<ade:template xmlns="http://www.w3.org/1999/xhtml" 
   xmlns:ade="http://ns.adobe.com/2006/ade" 
   xmlns:fo="http://www.w3.org/1999/XSL/Format">

   <fo:layout-master-set>
      <fo:simple-page-master master-name="single_column" margin-bottom="2em" 
         margin-top="2em" margin-left="2em" margin-right="2em">
         <fo:region-body/>
      </fo:simple-page-master>

      <fo:simple-page-master master-name="single_column_head" margin-bottom="2em" 
         margin-top="2em" margin-left="2em" margin-right="2em">
         <fo:region-before extent="8em"/>
         <fo:region-body margin-top="8em"/>
      </fo:simple-page-master>

      <fo:simple-page-master master-name="two_column" margin-bottom="2em" 
         margin-top="2em" margin-left="2em" margin-right="2em">
         <fo:region-body column-count="2" column-gap="3em"/>
      </fo:simple-page-master>

      <fo:simple-page-master master-name="two_column_head" margin-bottom="2em" 
         margin-top="2em" margin-left="2em" margin-right="2em">
         <fo:region-before extent="8em"/>
         <fo:region-body column-count="2" margin-top="8em" column-gap="3em"/>
      </fo:simple-page-master>

      <fo:simple-page-master master-name="three_column" margin-bottom="2em" 
         margin-top="2em" margin-left="2em" margin-right="2em">
         <fo:region-body column-count="3" column-gap="3em"/>
      </fo:simple-page-master>

      <fo:simple-page-master master-name="three_column_head" margin-bottom="2em" 
         margin-top="2em" margin-left="2em" margin-right="2em">
         <fo:region-before extent="8em"/>
         <fo:region-body column-count="3" margin-top="8em" column-gap="3em"/>
      </fo:simple-page-master>

      <fo:page-sequence-master>
         <fo:repeatable-page-master-alternatives>
            <fo:conditional-page-master-reference 
               master-reference="three_column_head" page-position="first" 
               ade:min-page-width="80em"/>
            <fo:conditional-page-master-reference 
               master-reference="three_column" ade:min-page-width="80em"/>
            <fo:conditional-page-master-reference 
               master-reference="two_column_head" page-position="first" 
               ade:min-page-width="50em"/>
            <fo:conditional-page-master-reference 
               master-reference="two_column" ade:min-page-width="50em"/>
            <fo:conditional-page-master-reference 
               master-reference="single_column_head" page-position="first"/>
            <fo:conditional-page-master-reference 
               master-reference="single_column"/>
         </fo:repeatable-page-master-alternatives>
      </fo:page-sequence-master>
   </fo:layout-master-set>

   <ade:style>
      <ade:styling-rule selector="#header" display="adobe-other-region" 
         adobe-region="xsl-region-before"/>
   </ade:style>

</ade:template>
'''

# OPF
#manifest_items = [
#     { 'id':'ncx', 'href':'toc.ncx', 'media-type':'text/html' },
#     { 'id':'cover', 'href':'title.html', 'media-type':'application/xhtml+xml' },
#     { 'id':'content', 'href':'content.html', 'media-type':'application/xhtml+xml' },
#     { 'id':'cover-image', 'href':'images/cover.png', 'media-type':'image/png' },
#     { 'id':'css', 'href':'stylesheet.css', 'media-type':'text/css' },
# spine_items = [
#     { 'idref':'book' }
#     { 'idref':'cover', 'linear':'no' },
#     { 'idref':'content' }
# guide_items = [
#     { 'href':'title.html', 'type':'cover', 'title':'cover' }
# cover     the book cover(s), jacket information, etc.
# title-page   page with possibly title, author, publisher, and other metadata
# toc   table of contents
# index   back-of-book style index
# glossary   
# acknowledgements   
# bibliography   
# colophon   
# copyright-page   
# dedication   
# epigraph   
# foreword   
# loi   list of illustrations
# lot   list of tables
# notes   
# preface   
# text   First "real" page of content (e.g. "Chapter 1") 
#
# NCX navpoints = [
#     { 'id':'navpoint-1', 'playOrder':'1', 'text':'Book', 'content':'book.html' },
#     { 'id':'navpoint-1', 'playOrder':'1', 'text':'Book Cover', 'content':'title.html' },
#     { 'id':'navpoint-2', 'playOrder':'2', 'text':'Contents', 'content':'content.html' },
# CAN NEST NAVPOINTS

if __name__ == '__main__':
    sys.stderr.write('I\'m a module.  Don\'t run me directly!')
    sys.exit(-1)

