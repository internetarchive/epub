#!/usr/bin/python

import sys
import getopt
import re

from lxml import etree
from lxml import objectify

# remove me for faster execution
debugme = True
if debugme:
    from  pydbgr.api import debug
    def assert_d(expr):
        if not expr:
            debug()
else:
    def debug():
        pass
    def assert_d(expr):
        pass

def usage():
    print 'usage: visualize_abbyy.py abbyy.xml scandata.xml'


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hf:b",
                                   ["help", "food="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt == "-b":
            print "beautiful"
        elif opt in ("-f", "--food"):
            print "food: " + arg

    if len(args) != 2:
        usage()
        sys.exit(-1)

    visualize(args[0], args[1])

abbyyns="{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}"
abyns = abbyyns
import Image
import ImageDraw
import ImageFont 
import color
from color import color as c
def visualize(abbyy_xml, scandata_xml):
    scandata = objectify.parse(scandata_xml)
    context = etree.iterparse(abbyy_xml, tag=abbyyns+'page')
    info = scan_pages(context, scandata)

def draw_rect(draw, el, sty, use_coords=None):
    if sty['width'] == 0:
        return
    
    lt, rb = use_coords if use_coords is not None else tag_coords(el)

    x1, y1 = lt
    x2, y2 = rb

    enclosing = None
    if use_coords is None:
        enclosing = enclosing_tag(el)
    if enclosing is not None and enclosing.get('t') is not None:
        elt, erb = tag_coords(enclosing)
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
    
def tag_coords(tag):
    t = int(tag.get('t'))
    b = int(tag.get('b'))
    l = int(tag.get('l'))
    r = int(tag.get('r'))
    return ((l, t), (r, b))

def four_coords(tag):
    l = int(tag.get('l'))
    t = int(tag.get('t'))
    r = int(tag.get('r'))
    b = int(tag.get('b'))
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
    'rect' : { 'col':color.orange, 'width':0, 'offset':-4, 'margin':10 },
    'par' : { 'col':color.green, 'width':2, 'offset':0, 'margin':10 },
    'line' : { 'col':color.blue, 'width':1, 'offset':0, 'margin':10 },
    }

def nons(tag):
    return re.sub('{.*}', '', tag)

def render(draw, el, expected, use_coords=None):
    shorttag = nons(el.tag)
    if (shorttag != 'block'):
        assert_d(shorttag == expected)
    sty = styles[expected]
    draw_rect(draw, el, sty, use_coords)

def box_from_par(par):
    if len(par) > 0:
        (o_l, o_t), (o_r, o_b) = tag_coords(par[0])
        for line in par:
            (l, t), (r, b) = tag_coords(line)
            o_l = l if (l - o_l < 0) else o_l
            o_t = t if (t - o_t < 0) else o_t
            o_r = r if (o_r - r < 0) else o_r
            o_b = b if (o_b - b < 0) else o_b
        return (o_l, o_t), (o_r, o_b)
    else:
        return None

import font
def scan_pages(context, scandata):
    scandata_pages = scandata.getroot().pageData.page
    i = 0
    f = ImageFont.load_default()
#    f = ImageFont.load('/Users/mccabe/s/archive/epub/Times-18.bdf')
    for event, page in context:
        image = Image.new('RGB',
                          (int(page.get('width')),
                           int(page.get('height'))))
        if i < 0:
            i += 1
            continue

        if i > 0:
        # orig page image
#         imfile = "jp2/littleroadstoryo00hick_" + str(i).zfill(4) + ".png"
            imfile = "png/proteusframebuilding_" + str(i).zfill(4) + ".png"
#         print imfile
            page_image = Image.open(imfile)
#         image.paste(page_image, None)
            image = Image.blend(image, page_image, .1)
        draw = ImageDraw.Draw(image)
        
        for block in page:
            if block.get('blockType') == 'Text':
                render(draw, block, 'block_text')    
            else:
                render(draw, block, 'block_picture')
                if i > 0:
                    cropped = page_image.crop(four_coords(block))
                    image.paste(cropped, four_coords(block))
            for el in block:
                if el.tag == abyns+'region':
                    for rect in el:
#                         debug()
                        render(draw, rect, 'rect')
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
                                f = font.get_font(font_name, font_size)

                                for cp in fmt:
                                    assert_d(cp.tag == abyns+'charParams')
                                    draw.text((int(cp.get('l')),
                                               int(cp.get('b'))),
                                              cp.text.encode('utf-8'),
                                              font=f,
                                              fill=color.white)
                elif (el.tag == abyns+'row'):
                    pass
                else:
                    print('unexpected tag type' + el.tag)
                    sys.exit(-1)

        if not include_page(scandata_pages[i]):
            draw.line([(0, 0), image.size], width=50, fill=color.red)
        
        image.save('img' + scandata_pages[i].get('leafNum') + '.png')
#         if i > 10:
#             break
        print i
        page.clear()
        i += 1
    return None

def include_page(page):
    add = page.find('addToAccessFormats')
    if add is not None and add.text == 'true':
        return True
    else:
        return False


if __name__ == '__main__':
    main(sys.argv[1:])
