#!/usr/bin/python

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
    def __init__(self, out_name, metadata, content_dir=''):
        self.dt = datetime.now()
        self.z = zipfile.ZipFile(out_name, 'w')
        self.content_dir = content_dir
        self.book_id = common.get_metadata_tag_data(metadata, 'identifier')
        self.title = common.get_metadata_tag_data(metadata, 'title')
        self.author = common.get_metadata_tag_data(metadata, 'author')
        self.nav_number = 1

        self.opf_file = self.book_id + '_daisy.opf'

        self.dtbook_file = self.book_id + '_daisy.xml'
        self.dtbook, self.dtbook_book_el = make_dtbook(self.book_id, self.title)

        self.smil_file = self.book_id + '_daisy.smil'
        self.smil, self.smil_seq_el = make_smil(self.book_id)

        self.ncx_file = self.book_id + '_daisy.ncx'
        self.ncx, self.ncx_navmap_el, self.ncx_pagelist_el = make_ncx(
            self.book_id, self.title, self.author)

        self.tag_stack = [self.dtbook_book_el]
        self.navpoint_stack = [self.ncx_navmap_el]

        self.id_index = 1

        # style sheet
        for content in ['daisy.css', 'daisyTransform.xsl',
                        'dtbook-2005-3.dtd', 'html.css']:
            content_src = os.path.join(sys.path[0], 'daisy', content)
            content_str = open(content_src, 'r').read()
            self.add(self.content_dir + content, content_str)

        self.manifest_items = [
            { 'id':'xml',
              'href':self.dtbook_file,
              'media-type':'application/x-dtbook+xml'
              },
            { 'id':'opf',
              'href':self.book_id + '_daisy.opf',
              'media-type':'text/xml'
              },
            { 'id':'ncx',
              'href':self.ncx_file,
              'media-type':'application/x-dtbncx+xml'
              },
            { 'id':'smil',
              'href':self.smil_file,
              'media-type':'application/smil'
              },
            { 'id':'daisyTransform',
              'href':'daisyTransform.xsl',
              'media-type':'text/xsl'
              },
            { 'id':'daisyCss',
              'href':'daisy.css',
              'media-type':'text/css'
              },
            { 'id':'htmlCss',
              'href':'html.css',
              'media-type':'text/css'
              },
            ]

        self.page_items = []
        self.navpoints = []


    def push_tag(self, tag, text='', attrs={}):
        # tag is e.g. frontmatter, bodymatter, rearmatter, level, etc.
        id_str, dtb_el = self.add_tag(tag, text, attrs)
        self.tag_stack.append(dtb_el)
        return id_str


    def pop_tag(self):
        self.tag_stack.pop()


    def add_tag(self, tag, text='', attrs={}):
        id_str = tag + '_' + (str(self.id_index).zfill(5))
        attrs['id'] = id_str
        if len(text) > 0:
            smil_par_el = etree.SubElement(self.smil_seq_el, 'par',
                                           { 'id':id_str, 'class':tag } )
            etree.SubElement(smil_par_el, 'text',
                             { 'src':self.dtbook_file + '#' + id_str,
                               'region':'textRegion' })
            attrs['smilref'] = self.smil_file + '#' + id_str
        current_dtb_el = self.tag_stack[-1]

        dtb_el = etree.SubElement(current_dtb_el, tag, attrs)
        if len(text) > 0:
            dtb_el.text = text

        self.id_index += 1
        return id_str, dtb_el


    def add_navpoint(self, ltag, htag, text):
        level = str(len(self.navpoint_stack))
        level_id_str = self.push_tag(ltag + level)
        htag_id_str, htag_dtb_el = self.add_tag(htag + level, text)
        current_navpoint_el = self.navpoint_stack[-1]
        navpoint_el = etree.SubElement(current_navpoint_el, 'navPoint',
                                       { 'id':level_id_str,
                                         'class':'navpoint-level-level' + level,
                                         'playOrder':str(self.nav_number) })
        navlabel_el = etree.SubElement(navpoint_el, 'navLabel')
        etree.SubElement(navlabel_el, 'text').text = text
        etree.SubElement(navpoint_el, 'content',
                         { 'src':self.smil_file + '#' + htag_id_str })
        self.nav_number += 1
        return navpoint_el


    def push_navpoint(self, ltag, htag, text):
        navpoint_el = self.add_navpoint(ltag, htag, text)
        self.navpoint_stack.append(navpoint_el)


    def pop_navpoint(self):
        return self.navpoint_stack.pop()


    def add_pagetarget(self, name, value, type='normal'):
        pagenum_id, pagenum_el = self.add_tag('pagenum', name, { 'page':type })

        pagetarget_el = etree.SubElement(self.ncx_pagelist_el,
                                         'pageTarget',
                                         { 'id':pagenum_id,
                                           'value':str(value),
                                           'type':type,
                                           'playOrder':str(self.nav_number) })
        navlabel_el = etree.SubElement(pagetarget_el, 'navLabel')
        etree.SubElement(navlabel_el, 'text').text = name
        etree.SubElement(pagetarget_el, 'content',
                         { 'src':self.smil_file + '#' + pagenum_id })
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
        tree_str = make_opf(metadata, self.manifest_items)
        self.add(self.content_dir + self.opf_file, tree_str)
        
        tree_str = common.tree_to_str(self.ncx)
        self.add(self.content_dir + self.ncx_file, tree_str)

        tree_str = common.tree_to_str(self.dtbook)
        self.add(self.content_dir + self.dtbook_file, tree_str)

        tree_str = common.tree_to_str(self.smil)
        self.add(self.content_dir + self.smil_file, tree_str)

        self.z.close()


dc = 'http://purl.org/dc/elements/1.1/'
dcb = '{' + dc + '}'
def make_opf(metadata,
             manifest_items):
    xml = """<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE package PUBLIC "+//ISBN 0-9673008-1-9//DTD OEB 1.2 Package//EN"
"http://openebook.org/dtds/oeb-1.2/oebpkg12.dtd">
<package xmlns="http://openebook.org/namespaces/oeb-package/1.0/"
unique-identifier="bookid"/>
"""
    tree = etree.parse(StringIO(xml))
    root_el = tree.getroot()
    metadata_el = etree.SubElement(root_el, 'metadata')
    dc_metadata_el = etree.SubElement(metadata_el, 'dc-metadata',
        nsmap={ 'dc':dc,
            'oebpackage':'http://openebook.org/namespaces/oeb-package/1.0/' })
    el = etree.SubElement(dc_metadata_el, dcb + 'Format')
    el.text = 'ANSI/NISO Z39.86-2005'
    for md in metadata:
        tagname = md['tag']
        if not tagname in [ 'title', 'creator', 'subject', 'description',
                           'publisher', 'contributor', 'date', 'type',
                           'format', 'identifier', 'source', 'language',
                           'relation','coverage', 'rights' ]:
            continue
        dctag = dcb + tagname[:1].upper() + tagname[1:]
        if tagname == 'identifier':
            el = etree.SubElement(dc_metadata_el, dctag,
                                  { 'id':'bookid' })
#             el.text = md['text'] + xtra
            el.text = md['text']
        else:
            el = etree.SubElement(dc_metadata_el, dctag)
            el.text = md['text']
    x_metadata_el = etree.SubElement(metadata_el, 'x-metadata')
    el = etree.SubElement(x_metadata_el, 'meta',
                          { 'name':'dtb:multimediaType', 'content':'textNCX' })
    el = etree.SubElement(x_metadata_el, 'meta',
                          { 'name':'dtb:multimediaContent', 'content':'text' })
    el = etree.SubElement(x_metadata_el, 'meta',
                          { 'name':'dtb:totalTime', 'content':'0' })

    manifest_el = etree.SubElement(root_el, 'manifest')
    for item in manifest_items:
        etree.SubElement(manifest_el, 'item', item)

    spine_el = etree.SubElement(root_el, 'spine')
    etree.SubElement(spine_el, 'itemref',
                     { 'idref':'smil' })

    tree = etree.ElementTree(root_el)
    return common.tree_to_str(tree)


def make_dtbook(book_id, title):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE dtbook SYSTEM "dtbook-2005-3.dtd">
<dtbook xmlns="http://www.daisy.org/z3986/2005/dtbook/" version="2005-3"/>
"""
    tree = etree.parse(StringIO(xml))
    root_el = tree.getroot()

    # Manually add these, as they seem to get dropped if in parsed xml above.
    pi = etree.ProcessingInstruction('xml-stylesheet',
        'type="text/css" href="daisy.css" media="screen"')
    root_el.addprevious(pi)
    pi = etree.ProcessingInstruction('xml-stylesheet',
        'type="text/xsl" href="daisyTransform.xsl" media="screen"')
    root_el.addprevious(pi)
    
    head_el = etree.SubElement(root_el, 'head')
    etree.SubElement(head_el, 'meta',
                     { 'name':'dtb:uid',
                       'content':book_id })
    etree.SubElement(head_el, 'meta',
                     { 'name':'dc:Title',
                       'content':title })
    # <book id="book_201979196" xml:space="preserve">
    book_el = etree.SubElement(root_el, 'book')
    return tree, book_el


def make_smil(book_id):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE smil PUBLIC "-//NISO//DTD dtbsmil 2005-2//EN" "http://www.daisy.org/z3986/2005/dtbsmil-2005-2.dtd">

<smil xmlns="http://www.w3.org/2001/SMIL20/"/>
"""
    tree = etree.parse(StringIO(xml))
    root_el = tree.getroot()
    head_el = etree.SubElement(root_el, 'head')
    etree.SubElement(head_el, 'meta',
                     { 'name':'dtb:uid',
                       'content':book_id })
    etree.SubElement(head_el, 'meta',
                     { 'name':'dtb:generator', 'content':'archive.org' }) # XXX
    etree.SubElement(head_el, 'meta',
                     { 'name':'dtb:totalElapsedTime', 'content':'0' })
    layout_el = etree.SubElement(head_el, 'layout')
    etree.SubElement(layout_el, 'region',
                     { 'id':'textRegion', 'fit':'hidden',
                       'showBackground':'always',
                       'height':'auto', 'width':'auto',
                       'bottom':'auto', 'top':'auto',
                       'left':'auto', 'right':'auto' })
    # 'customAttributes' el = required?
    body_el = etree.SubElement(root_el, 'body')
    seq_el = etree.SubElement(body_el, 'seq',
                              { 'id':'toplevel_seq_id' })
    return tree, seq_el


def make_ncx(book_id, title, author):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"/>
"""
    tree = etree.parse(StringIO(xml))
    root_el = tree.getroot()
    head = etree.SubElement(root_el, 'head')
    metas = [
        { 'name' : 'dtb:uid',
          'content':book_id },
        { 'name' : 'dtb:depth', 'content' : '1' },
        { 'name' : 'dtb:totalPageCount', 'content' : '0' },
        { 'name' : 'dtb:maxPageNumber', 'content' : '0' },
        ]
    for item in metas:
        etree.SubElement(head, 'meta', item)
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


#     # pageList element
#     if len(page_items) > 0:
#         pagelist = etree.SubElement(root_el, 'pageList',
#                                     { 'id':'page-mapping', 'class':'pagelist' })
#         navlabel = etree.SubElement(pagelist, 'navLabel')
#         text = etree.SubElement(navlabel, 'text')
#         text.text = 'Pages'
#         for item in page_items:
#             id = 'page-' + item['name']
#             pagetarget = etree.SubElement(pagelist, 'pageTarget',
#                                           { 'id':id, 'value':str(item['value']),
#                                             'type':item['type'],
#                                             'playOrder':str(item['playOrder']) })
#             navlabel = etree.SubElement(pagetarget, 'navLabel')
#             etree.SubElement(navlabel, 'text').text = 'Page ' + item['name']
#             etree.SubElement(pagetarget, 'content', src=item['href'])

    return tree, navmap_el, pagelist_el


if __name__ == '__main__':
    sys.stderr.write('I\'m a module.  Don\'t run me directly!')
    sys.exit(-1)
