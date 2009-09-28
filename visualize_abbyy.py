#!/usr/bin/python

import sys
import getopt
import re
import os

from lxml import etree
from lxml import objectify

import iarchive
import common

outdir='viz'

kdu_reduce = 2
scale = 2 ** kdu_reduce
s = scale

from debug import debug, debugging, assert_d

def usage():
    print 'usage: visualize_abbyy.py'

def main(argv):
    if not os.path.isdir('./' + outdir+ '/'):
        os.mkdir('./' + outdir + '/')

    id = common.get_book_id()
    iabook = iarchive.Book(id, '.')
    visualize(iabook)

abbyyns="{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}"
abyns = abbyyns
import Image
import ImageDraw
import ImageFont 
import color
from color import color as c
def visualize(iabook):
#    scandata = objectify.parse(iabook.get_scandata_path()).getroot()
    scandata = iabook.get_scandata()
    context = etree.iterparse(iabook.get_abbyy(), tag=abbyyns+'page')
    info = scan_pages(context, scandata, iabook)

def draw_rect(draw, el, sty, use_coords=None):
    if sty['width'] == 0:
        return
    
    lt, rb = use_coords if use_coords is not None else tag_coords(el, s)

    x1, y1 = lt
    x2, y2 = rb

    enclosing = None
    if use_coords is None:
        enclosing = enclosing_tag(el)
    if enclosing is not None and enclosing.get('t') is not None:
        elt, erb = tag_coords(enclosing, s)
        ex1, ey1 = elt
        ex2, ey2 = erb

        margin = sty['margin']

        near = 3

        x1 = x1 + margin if x1 - ex1 < near else x1
        x2 = x2 - margin if ex2 - x2 < near else x2
        y1 = y1 + margin if y1 - ey1 < near else y1
        y2 = y2 - margin if ey2 - y2 < near else y2

#     x1 += sty['offset']
#     y1 += sty['offset']
#     x2 += sty['offset']
#     y2 += sty['offset']
    draw.line([(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)],
              width=sty['width'], fill=sty['col'])
    
def tag_coords(tag, s):
    t = int(tag.get('t'))/s
    b = int(tag.get('b'))/s
    l = int(tag.get('l'))/s
    r = int(tag.get('r'))/s
    return ((l, t), (r, b))

def four_coords(tag, s):
    l = int(tag.get('l'))/s
    t = int(tag.get('t'))/s
    r = int(tag.get('r'))/s
    b = int(tag.get('b'))/s
    return l, t, r, b

def enclosing_tag(tag):
    tag_with_coords = tag
    while tag_with_coords is not None:
        tag_with_coords = tag.getparent()
        if tag_with_coords is not None and tag.get('t') is not None:
            break
    return tag_with_coords

styles = {
    'block_text' : { 'col':color.yellow, 'width':1, 'offset':0, 'margin':10 },
    'block_picture' : { 'col':color.red, 'width':1, 'offset':7, 'margin':10 },
    'block_table' : { 'col':color.purple, 'width':1, 'offset':7, 'margin':10 },
    'rect' : { 'col':color.orange, 'width':0, 'offset':-4, 'margin':10 },
    'par' : { 'col':color.green, 'width':2, 'offset':0, 'margin':10 },
    'line' : { 'col':color.blue, 'width':1, 'offset':0, 'margin':10 },
    }

def nons(tag):
    return re.sub('{.*}', '', tag)

def render(draw, el, expected, use_coords=None):
    assert_tag(el, expected)
    sty = styles[expected]
    draw_rect(draw, el, sty, use_coords)

def assert_tag(el, expected):
    shorttag = nons(el.tag)
    if (shorttag != 'block'):
        assert_d(shorttag == expected)

def box_from_par(par):
    if len(par) > 0:
        (o_l, o_t), (o_r, o_b) = tag_coords(par[0], s)
        for line in par:
            (l, t), (r, b) = tag_coords(line, s)
            o_l = l if (l - o_l < 0) else o_l
            o_t = t if (t - o_t < 0) else o_t
            o_r = r if (o_r - r < 0) else o_r
            o_b = b if (o_b - b < 0) else o_b
        return (o_l, o_t), (o_r, o_b)
    else:
        return None

import os

import StringIO
import font
def scan_pages(context, scandata, iabook):
    book_id = iabook.get_book_id()
    scandata_pages = scandata.pageData.page
    try:
        # dpi isn't always there
        dpi = int(scandata.bookData.dpi.text)
    except AttributeError:
        dpi = 300
    i = 0
    f = ImageFont.load_default()
#    f = ImageFont.load('/Users/mccabe/s/archive/epub/Times-18.bdf')
    for event, page in context:
        page_scandata = iabook.get_page_data(i)
        def include_page(page):
            if page is None:
                return False
            add = page.find('addToAccessFormats')
            if add is None:
                add = page.addToAccessFormats
            if add is not None and add.text == 'true':
                return True
            else:
                return False
        if not include_page(page_scandata):
            i += 1
            continue

        orig_width = int(page.get('width'))
        orig_height = int(page.get('height'))
        width = orig_width / s
        height = orig_height / s
        
        image = Image.new('RGB', (width, height))

        page_image = None

        image_str = iabook.get_image(i, width, height, out_img_type='ppm')
        if image_str is not None:
            page_image = Image.open(StringIO.StringIO(image_str))
            (nw, nh) = page_image.size
            if nw != width or nh != height:
                page_image = page_image.resize((width, height))
#        image.paste(page_image, None)
            try:
                image = Image.blend(image, page_image, .2)
            except ValueError:
                print 'blending - images didn\'t match'
                debug()
                pass
                
        draw = ImageDraw.Draw(image)

        for block in page:
            if block.get('blockType') == 'Picture' and page_image is not None:
                cropped = page_image.crop(four_coords(block, scale))
                image.paste(cropped, four_coords(block, scale))
                
        for block in page:
            if block.get('blockType') == 'Text':
                render(draw, block, 'block_text')    
            if block.get('blockType') == 'Picture':
                render(draw, block, 'block_picture')
            if block.get('blockType') == 'Table':
                render(draw, block, 'block_table')
#             else:
#                 render(draw, block, 'block_picture')
#                 if i > 0:
#                     cropped = page_image.crop(four_coords(block))
#                     image.paste(cropped, four_coords(block))
            for el in block:
                if el.tag == abyns+'region':
                    pass
                elif el.tag == abyns+'row':
                    for cell in el:
                        for text in cell:
                            for par in text:
                                par_coords = box_from_par(par)
                                if par_coords is not None:
                                    render(draw, par, 'par', par_coords)
                                for line in par:
                                    render(draw, line, 'line');
                                    for fmt in line:
                                        assert_d(fmt.tag == abyns+'formatting')
                                        font_name = fmt.get('ff')
                                        font_size = fmt.get('fs')
                                        font_size = int(re.sub('\.', '', font_size))
                                        font_ital = (fmt.get('italic') == 'true')
                                        f = font.get_font(font_name, dpi / scale, font_size, font_ital)
                                        for cp in fmt:
                                            assert_d(cp.tag == abyns+'charParams')
                                            draw.text((int(cp.get('l'))/s,
                                                       int(cp.get('b'))/s),
                                                      cp.text.encode('utf-8'),
                                                      font=f,
                                                      fill=color.yellow)
                elif el.tag == abyns+'text':
                    for par in el:
                        par_coords = box_from_par(par)
                        if par_coords is not None:
                            render(draw, par, 'par', par_coords)
                        for line in par:
                            render(draw, line, 'line');
                            for fmt in line:
                                assert_d(fmt.tag == abyns+'formatting')
                                font_name = fmt.get('ff')
                                font_size = fmt.get('fs')
                                font_size = int(re.sub('\.', '', font_size))
                                font_ital = (fmt.get('italic') == 'true')
                                f = font.get_font(font_name, dpi / scale, font_size, font_ital)
                                for cp in fmt:
                                    assert_d(cp.tag == abyns+'charParams')
                                    draw.text((int(cp.get('l'))/s,
                                               int(cp.get('b'))/s),
                                              cp.text.encode('utf-8'),
                                              font=f,
                                              fill=color.yellow)
                elif (el.tag == abyns+'row'):
                    pass
                else:
                    print('unexpected tag type' + el.tag)
                    sys.exit(-1)

        if not include_page(scandata_pages[i]):
            draw.line([(0, 0), image.size], width=50, fill=color.red)
        
        image.save(outdir + '/img' + scandata_pages[i].get('leafNum') + '.png')
        print i
        page.clear()
        i += 1
    return None

def include_page(page):
    if page is None:
        return False
    add = page.find('addToAccessFormats')
    if add is None:
        add = page.addToAccessFormats
    if add is not None and add.text == 'true':
        return True
    else:
        return False



if __name__ == '__main__':
    main(sys.argv[1:])
