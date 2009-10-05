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
        self.nav_number = 1

        self.dtbook_file = self.book_id + '_daisy.xml'
        self.dtbook, self.dtbook_book_el = make_dtbook(self.book_id, self.title)
        self.tag_stack = [self.dtbook_book_el]

        self.smil_file = self.book_id + '_daisy.smil'
        self.smil, self.smil_seq_el = make_smil(self.book_id)

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
              'href':self.book_id + '_daisy.ncx',
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
        self.tag_stack.append(self.add_tag(tag, text, attrs))
        # tag is e.g. frontmatter, bodymatter, rearmatter, level, etc.


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
        el = etree.SubElement(self.tag_stack[-1], tag, attrs)
        if len(text) > 0:
            el.text = text

        self.id_index += 1
        return el


    def add_navpoint(self, text, content):
        # text='text':'Title Page',
        # content='title.html' }
        # navpoints added thru this interface are sequential -
        # id and playOrder are generated.
        self.navpoints.append({ 'text':text, 'content':content,
                                'playOrder':self.nav_number })
        self.nav_number += 1


    def add_page_item(self, name, value, href, type='normal'):
        # name='iii', value='3', href='part032.html#pgiii', type='front'
        # name='3', value='3', href='part042.html#pg3', type='normal'
        self.page_items.append({ 'name':name, 'value':value, 'href':href,
                                 'type':type, 'playOrder':self.nav_number })
        self.add_tag('pagenum', name, { 'page':type })
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
        self.add(self.content_dir + self.book_id + '_daisy.opf', tree_str)

        tree_str = make_ncx(self.navpoints, self.page_items, self.book_id)
        self.add(self.content_dir + self.book_id + '_daisy.ncx', tree_str)

        tree_str = common.tree_to_str(self.dtbook)
        self.add(self.content_dir + self.book_id + '_daisy.xml', tree_str)

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
                          { 'name':'dtb:totalElapsedTime', 'content':'0' })

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
    # 'layout' el = required?
    # 'customAttributes' el = required?
    body_el = etree.SubElement(root_el, 'body')
    seq_el = etree.SubElement(body_el, 'seq',
                              { 'id':'toplevel_seq_id' })
    return tree, seq_el


def make_ncx(navpoints, page_items, book_id):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"/>
"""
    tree = etree.parse(StringIO(xml))
    root = tree.getroot()
    head = etree.SubElement(root, 'head')
    metas = [
        { 'name' : 'dtb:uid',
          'content':book_id },
        { 'name' : 'dtb:depth', 'content' : '1' },
        { 'name' : 'dtb:totalPageCount', 'content' : '0' },
        { 'name' : 'dtb:maxPageNumber', 'content' : '0' },
        ]
    for item in metas:
        etree.SubElement(head, 'meta', item)
    doctitle = etree.SubElement(root, 'docTitle')
    etree.SubElement(doctitle, 'text').text = 'Hello World';

    # navMap element
    navmap = etree.SubElement(root, 'navMap')
    for item in navpoints:
        navpoint = etree.SubElement(navmap, 'navPoint',
                                    { 'id':'navpoint-' + str(item['playOrder']),
                                      'playOrder':str(item['playOrder']) })
        navlabel = etree.SubElement(navpoint, 'navLabel')
        etree.SubElement(navlabel, 'text').text = item['text']
         # XXX 'content' should be 'href'
        etree.SubElement(navpoint, 'content', src=item['content'])

    # pageList element
    if len(page_items) > 0:
        pagelist = etree.SubElement(root, 'pageList',
                                    { 'id':'page-mapping', 'class':'pagelist' })
        navlabel = etree.SubElement(pagelist, 'navLabel')
        text = etree.SubElement(navlabel, 'text')
        text.text = 'Pages'
        for item in page_items:
            id = 'page-' + item['name']
            pagetarget = etree.SubElement(pagelist, 'pageTarget',
                                          { 'id':id, 'value':str(item['value']),
                                            'type':item['type'],
                                            'playOrder':str(item['playOrder']) })
            navlabel = etree.SubElement(pagetarget, 'navLabel')
            etree.SubElement(navlabel, 'text').text = 'Page ' + item['name']
            etree.SubElement(pagetarget, 'content', src=item['href'])

    tree = etree.ElementTree(root)
    return common.tree_to_str(tree)


if __name__ == '__main__':
    sys.stderr.write('I\'m a module.  Don\'t run me directly!')
    sys.exit(-1)
