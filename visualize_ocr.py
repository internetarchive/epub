#!/usr/bin/python

import sys
import re
import os

try:
    from lxml import etree
except ImportError:
    sys.path.append('/petabox/sw/lib/lxml/lib/python2.5/site-packages') 
    from lxml import etree
from lxml import objectify

import iarchive
import common

from debug import debug, debugging, assert_d

opts = None


def legend():
    print 'legend: (for abbyy format)'
    print '    ta - align'
    print '    li - leftIndent'
    print '    ri - rightIndent'
    print '    si - startIndent'
    print '    ls - lineSpacing'
    print
    print 'Colors:'
    for sty_name in styles:
        print '    ' + styles[sty_name]['col'] + '  -  ' + sty_name

def main(argv):
    import optparse
    parser = optparse.OptionParser()
    parser = optparse.OptionParser(usage='usage: %prog [options]',
                                   version='%prog 0.1',
                                   description='A visualizer for '
                                   'coordinate-annotated OCR data.')
    def legend_callback(option, opt_str, value, parser):
        legend()
        sys.exit(0)
    parser.add_option('--legend', '-l',
                     action='callback',
                     callback=legend_callback,
                     help='Display legend information - for generated images')
    parser.add_option('--reduce',
                      action='store',
                      type='int',
                      metavar='n',
                      default=2,
                      help='For jp2 input images, reduce jp2 resolution '
                      'by 2 ^ n when reading '
                      'original image, for speed.  This also reduces the '
                      'output scale by 2 ^ n, unless otherwise specified '
                      'with --scale.')
    parser.add_option('--scale',
                      action='store',
                      type='int',
                      default=0,
                      help='Scale result images down from original scan '
                      'resolution.')
    parser.add_option('--last',
                      action='store',
                      type='int',
                      metavar='leaf',
                      default=0,
                      help='Stop generating output leaves '
                      'after the specified leaf')
    parser.add_option('--first',
                      action='store',
                      type='int',
                      metavar='leaf',
                      default=0,
                      help='Don\'t generate output leaves until the '
                      'specified leaf')
    parser.add_option('--leaf',
                      action='store',
                      type='int',
                      metavar='leaf',
                      default=0,
                      help='Only generate output for the specified leaf')
    parser.add_option('--text',
                      action='store_true',
                      default=False,
                      help='Generate output characters for OCRed '
                      'text in input files')
    parser.add_option('--outdir',
                      help='Output directory.  Default is source_type + \'_viz\'')
    parser.add_option('--source',
                      choices=['abbyy', 'pdftoxml', 'djvu'],
                      default='abbyy',
                      help='Which source to use for OCR data/coordinates.')
    parser.add_option('--show-opts',
                      action='store_true',
                      # help=optparse.SUPPRESS_HELP
                      help='Display parsed options/defaults and exit')
    global opts
    opts, args = parser.parse_args(argv)
    if opts.reduce < 0 or opts.reduce > 4:
        parser.error('--reduce must be between 0 and 4')
    if opts.scale == 0:
        opts.scale = 2 ** opts.reduce

    if opts.leaf != 0:
        if opts.first > 0 or opts.last > 0:
            parser.error('can\'t specify --last or --first with --leaf')
        opts.last = opts.first = opts.leaf

    if opts.source == 'djvu':
        parser.error('--source=djvu not supported at the moment')

    if opts.outdir is None:
        opts.outdir = opts.source + '_viz'

    if opts.show_opts:
        print 'Options: ' + str(opts)
        print 'Args: ' + str(args)
        sys.exit(0)

    parser.destroy()
    
    if not os.path.isdir('./' + opts.outdir + '/'):
        os.mkdir('./' + opts.outdir + '/')

    id = iarchive.infer_book_id()
    iabook = iarchive.Book(id, '', '.')
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
    if opts.source == 'abbyy':
        context = etree.iterparse(iabook.get_abbyy(), tag=abbyyns+'page')
    elif opts.source == 'pdfxml':
        context = etree.iterparse(iabook.get_pdfxml_xml(), tag='PAGE')
    elif opts.source == 'djvu':
        context = etree.iterparse(iabook.get_djvu_xml(), tag='OBJECT')
    info = scan_pages(context, scandata, iabook)


def has_coord(el):
    if opts.source == 'abbyy':
        return (el.get('t') is not None)
    elif opts.source == 'pdfxml':
        return (el.get('y') is not None)
    elif opts.source == 'djvu':
        raise 'djvuness not yet implemented here'


def get_coord(el, ltrb):
    def iget(ltrb):
        return int(math.floor(float(el.get(ltrb))))
    if opts.source == 'pdfxml':
        if ltrb == 't':
            return iget('y')
        elif ltrb == 'l':
            return iget('x')
        elif ltrb == 'r':
            return iget('x') + iget('width')
        elif ltrb == 'b':
            return iget('y') + iget('height')
    elif opts.source == 'djvu':
        raise 'djvuness not yet implemented here'
    else: # abbyy
        return el.get(ltrb)


def draw_rect(draw, el, sty, use_coords=None):
    col = color.color[sty['col']]
    if sty['width'] == 0:
        return
    
    lt, rb = use_coords if use_coords is not None else tag_coords(el, opts.scale)

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
              width=sty['width'], fill=col)
    
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

def center(tag, s):
    l, t, r, b = four_coords(tag, s)
    return l + (r - l) / 2, t + (b - t) / 2

def enclosing_tag(tag):
    tag_with_coords = tag
    while tag_with_coords is not None:
        tag_with_coords = tag.getparent()
        if tag_with_coords is not None and tag.get('t') is not None:
            break
    return tag_with_coords

styles = {
    'block_text' : { 'col':'yellow', 'width':1, 'offset':0, 'margin':10 },
    'block_picture' : { 'col':'red', 'width':1, 'offset':7, 'margin':10 },
    'block_table' : { 'col':'purple', 'width':1, 'offset':7, 'margin':10 },
    'rect' : { 'col':'orange', 'width':1, 'offset':-4, 'margin':10 },
    'par' : { 'col':'green', 'width':2, 'offset':0, 'margin':10 },
    'line' : { 'col':'blue', 'width':1, 'offset':0, 'margin':10 },
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
        (o_l, o_t), (o_r, o_b) = tag_coords(par[0], opts.scale)
        for line in par:
            (l, t), (r, b) = tag_coords(line, opts.scale)
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
    scandata_ns = iabook.get_scandata_ns()
    try:
        # dpi isn't always there
        dpi = int(scandata.bookData.dpi.text)
    except AttributeError:
        dpi = 300
    i = 0
    f = ImageFont.load_default()
#    f = ImageFont.load('/Users/mccabe/s/archive/epub/Times-18.bdf')
    for event, page in context:
        if opts.first > 0:
            if i < opts.first:
                i += 1
                continue
        orig_width = int(page.get('width'))
        orig_height = int(page.get('height'))
        orig_size = (orig_width, orig_height)
        requested_size = (orig_width / opts.scale, orig_height / opts.scale)
        
        image = Image.new('RGB', requested_size)
        image_str = iabook.get_page_image(i, requested_size,
                                          out_img_type='ppm',
                                          kdu_reduce=opts.reduce)
        page_image = None
        if image_str is not None:
            page_image = Image.open(StringIO.StringIO(image_str))
            if requested_size != page_image.size:
                page_image = page_image.resize(requested_size)
            try:
                image = Image.blend(image, page_image, .2)
            except ValueError:
                print 'blending - images didn\'t match'
                debug()
                pass
                
        draw = ImageDraw.Draw(image)
        for block in page:
            if block.get('blockType') == 'Picture' and page_image is not None:
                cropped = page_image.crop(four_coords(block, opts.scale))
                image.paste(cropped, four_coords(block, opts.scale))
                
        for block in page:
            blocktype = ''
            if block.get('blockType') == 'Text':
                blocktype = 'Text'
                render(draw, block, 'block_text')    
            if block.get('blockType') == 'Picture':
                blocktype = 'Picture'
                render(draw, block, 'block_picture')
            if block.get('blockType') == 'Table':
                blocktype = 'Table'
                render(draw, block, 'block_table')
#             else:
#                 render(draw, block, 'block_picture')
#                 if i > 0:
#                     cropped = page_image.crop(four_coords(block))
#                     image.paste(cropped, four_coords(block))
            for el in block:
                if el.tag == abyns+'region':
                    for rect in el:
                        if rect.tag != abyns+'rect':
                            raise 'found non-rect in region: ' + rect.tag
                        render(draw, rect, 'rect')
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
                                        f = font.get_font(font_name, dpi / opts.scale, font_size, font_ital)
                                        for cp in fmt:
                                            assert_d(cp.tag == abyns+'charParams')
                                            draw.text((int(cp.get('l')) / opts.scale,
                                                       int(cp.get('b')) / opts.scale),
                                                      cp.text.encode('utf-8'),
                                                      font=f,
                                                      fill=color.yellow)
                elif el.tag == abyns+'text':
                    for par in el:
                        par_coords = box_from_par(par)
                        if par_coords is not None:
                            render(draw, par, 'par', par_coords)
                            tl, rb = par_coords

                            t = ''
                            for att, nick in [ ('align', 'ta'),
                                               ('leftIndent', 'li'),
                                               ('rightIndent', 'ri'),
                                               ('startIndent', 'si'),
                                               ('lineSpacing', 'ls') ]:
                                att_txt = par.get(att)
                                if att_txt is not None:
                                    t += nick + ':' + att_txt + ' '
                            if len(t) > 0:
                                f = font.get_font("Courier", dpi / opts.scale, 12)
                                draw.text(tl, t, font=f, fill=color.green)
                        for line in par:
                            render(draw, line, 'line');
                            for fmt in line:
                                assert_d(fmt.tag == abyns+'formatting')
                                font_name = fmt.get('ff')
                                font_size = fmt.get('fs')
                                font_size = int(re.sub('\.', '', font_size))
                                font_ital = (fmt.get('italic') == 'true')
                                f = font.get_font(font_name, dpi / opts.scale, font_size, font_ital)
                                for cp in fmt:
                                    assert_d(cp.tag == abyns+'charParams')
                                    if opts.text:
                                        draw.text((int(cp.get('l')) / opts.scale,
                                                   int(cp.get('b')) / opts.scale),
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

        page_scandata = iabook.get_page_scandata(i)
        if page_scandata is not None:
            t = page_scandata.pageType.text

#             pageno_string = page_scandata.pageNumber.text
            pageno = page_scandata.find(scandata_ns + 'pageNumber')
            if pageno:
                pageno_string = pageno.text    
                t += ' ' + pageno_string

            handside = page_scandata.find(scandata_ns + 'handSide')
            if handside:
                t += ' ' + handside.text

            f = font.get_font("Courier", dpi / opts.scale, 12)
            page_w, page_h = image.size
            draw.text((.02 * dpi,
                       .02 * dpi),
                      t.encode('utf-8'),
                      font=f,
                      fill=color.green)

        image.save(opts.outdir + '/img' + scandata_pages[i].get('leafNum').zfill(3) + '.png')
        print 'leaf index: ' + str(i)
        page.clear()
        i += 1
        if opts.last > 0:
            if i > opts.last:
                sys.exit(0)
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
