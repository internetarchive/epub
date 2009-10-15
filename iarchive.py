#!/usr/bin/python

import sys
import getopt
import re
import gzip
import os
import zipfile

try:
    from lxml import etree
except ImportError:
    sys.path.append('/petabox/sw/lib/lxml/lib/python2.5/site-packages') 
    from lxml import etree
from lxml import objectify

from debug import debug, debugging, assert_d

class Book(object):
    def __init__(self, book_id, document, book_path):
        self.book_id = book_id
        self.document = document
        self.book_path = book_path
        if not os.path.exists(book_path):
            raise Exception('Can\'t find book path "' + book_path + '"')
        self.scandata = None
        self.images_type = 'unknown'
        if os.path.exists(os.path.join(book_path, book_id + '_jp2.zip')):
            self.images_type = 'jp2.zip'
        elif os.path.exists(os.path.join(book_path, book_id + '_tif.zip')):
            self.images_type = 'tif.zip'
#         else:
#             raise Exception('Can\'t find book images')
        

    def get_book_id(self):
        return self.book_id

    def get_book_path(self):
        return self.book_path

    def get_scandata_path(self):
        paths = [
            os.path.join(self.book_path, self.book_id + '_scandata.xml'),
            os.path.join(self.book_path, 'scandata.xml'),
            os.path.join(self.book_path, 'scandata.zip'),
            ]
        for sd_path in paths:
            if os.path.exists(sd_path):
                return sd_path
        raise Exception('No scandata found')

    def get_scandata(self):
        if self.scandata is None:
            scandata_path = self.get_scandata_path()
            (base, ext) = os.path.splitext(scandata_path)
            if ext.lower() == '.zip':
                z = zipfile.ZipFile(scandata_path, 'r')
                scandata_str = z.read('scandata.xml')
                z.close()
                self.scandata = objectify.fromstring(scandata_str)
                self.scandata_pages = self.scandata.pageData.page
            else:
                self.scandata = objectify.parse(self.
                                                get_scandata_path()).getroot()
                self.scandata_pages = self.scandata.xpath('/book/pageData/page')
            self.leaves = {}
            for page in self.scandata_pages:
                self.leaves[int(page.get('leafNum'))] = page
        return self.scandata

    def get_scandata_pages(self):
        self.get_scandata()
        return self.scandata_pages

    def get_page_scandata(self, i):
        self.get_scandata()
        return self.scandata_pages[int(i)]
#     scandata_pages = scandata.xpath('/book/pageData/page')
#     if scandata_pages is None or len(scandata_pages) == 0:
#         scandata_pages = scandata.pageData.page

    def get_page_data_from_leafno(self, leaf):
        if leaf in self.leaves:
            return self.leaves[leaf]
        else:
            return None

    def get_leafno_for_page(self, i):
        return int(self.get_page_scandata(i).get('leafNum'))

    def get_metadata(self):
        md_path = os.path.join(self.book_path, self.book_id + '_meta.xml')
        md = objectify.parse(md_path).getroot()
        result = []
        for el in md.iterchildren():
            if el.tag == 'language':
                result_text = iso_639_23_to_iso_639_1(el.text)
            else:
                result_text = el.text
            result.append({ 'tag':el.tag, 'text':result_text })
        return result

    def get_toc(self):
        toc_path = os.path.join(self.book_path, self.book_id + '_toc.xml')
        if not os.path.exists(toc_path):
            return None
        toc = objectify.parse(toc_path).getroot()
        result = {}
        for el in toc.iterchildren():
            result[el.get('page')] = el.get('title')
        return result

    def get_abbyy(self):
        abbyy_gz = os.path.join(self.book_path, self.book_id + '_abbyy.gz')
        if os.path.exists(abbyy_gz):
            return gzip.open(abbyy_gz, 'rb')
        abbyy_zip = os.path.join(self.book_path, self.book_id + '_abbyy.zip')
        if os.path.exists(abbyy_zip):
            return os.popen('unzip -p ' + abbyy_zip + ' ' + self.book_id + '_abbyy.xml')
#             z = zipfile.ZipFile(abbyy_zip, 'r')
#             return z.open(self.book_id + '_abbyy.xml') # only in 2.6
        abbyy_xml = os.path.join(self.book_path, self.book_id + '_abbyy.xml')
        if os.path.exists(abbyy_xml):
            return open(abbyy_xml, 'r')
        raise 'No abbyy file found'

    # get python string with image data - from .jp2 image in zip
    # finds appropriate leaf number for supplied page index
    def get_page_image(self, i, width=700, height=900,
                       quality=90,
                       region='{0.0,0.0},{1.0,1.0}',
                       out_img_type='jpg'):
        leafno = self.get_leafno_for_page(i)
#         debug()
        if self.images_type == 'jp2.zip':
            zipf = os.path.join(self.book_path,
                                self.book_id + '_jp2.zip')
            image_path = (self.book_id + '_jp2/' + self.book_id + '_'
                          + str(leafno).zfill(4) + '.jp2')
            in_img_type = 'jp2'
        elif self.images_type == 'tif.zip':
            zipf  = os.path.join(self.book_path,
                                 self.book_id + '_tif.zip')
            image_path = (self.book_id + '_tif/' + self.book_id + '_'
                          + str(leafno).zfill(4) + '.tif')
            in_img_type = 'tif'
        else:
            return None
        try:
            z = zipfile.ZipFile(zipf, 'r')
            info = z.getinfo(image_path) # for to check it exists
            z.close()
        except KeyError:
            return None
        return image_from_zip(zipf, image_path,
                              width, height, quality, region,
                              in_img_type, out_img_type)

if not os.path.exists('/tmp/stdout.ppm'):
    os.symlink('/dev/stdout', '/tmp/stdout.ppm')
if not os.path.exists('/tmp/stdout.bmp'):
    os.symlink('/dev/stdout', '/tmp/stdout.bmp')
 
# get python string with image data - from .jp2 image in zip
def image_from_zip(zipf, image_path,
                   width, height, quality, region,
                   in_img_type, out_img_type):
    if not os.path.exists(zipf):
        raise Exception('Zipfile missing')
    if region != '{0.0,0.0},{1.0,1.0}':
        raise Exception('Um, only whole image grabbage supported 4 now')

    scale = ' | pnmscale -quiet -xysize ' + str(width) + ' ' + str(height)
#     scale = ' | pamscale -quiet -xyfit ' + str(width) + ' ' + str(height)
    if out_img_type == 'jpg':
        cvt_to_out = ' | pnmtojpeg -quiet -quality ' + str(quality)
    elif out_img_type == 'ppm':
        cvt_to_out = ' | ppmtoppm -quiet'
    else:
        raise Exception('unrecognized out img type')
    if in_img_type == 'jp2':
        output = os.popen('unzip -p ' + zipf + ' ' + image_path
                        + ' | kdu_expand -region "' + region + '"'
                        +   ' -reduce 2 '
                        +   ' -no_seek -i /dev/stdin -o /tmp/stdout.bmp'
                        + ' | bmptopnm -quiet '
                        + ' | pnmscale -quiet '
                        +   ' -xysize ' + str(width) + ' ' + str(height)
                        + scale
                        + cvt_to_out)
    elif in_img_type == 'tif':
        import tempfile
        t_handle, t_path = tempfile.mkstemp()
#         t_handle.close()
        output = os.popen('unzip -p ' + zipf + ' ' + image_path
                        + ' > ' + t_path)
        output.read()
        output = os.popen('tifftopnm -quiet ' + t_path
#                         + ' | pamcut <blah> '
                        + scale
                        + cvt_to_out)
    else:
        raise Exception('unrecognized in img type')
    return output.read()

# ' | pnmscale -quiet -xysize ' + str(width) + ' ' + str(height)

# Adapted from http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
def iso_639_23_to_iso_639_1(marc_code):
    mapping = {
        'aar':'aa',
        'abk':'ab',
        'ave':'ae',
        'afr':'af',
        'aka':'ak',
        'amh':'am',
        'arg':'an',
        'ara':'ar',
        'asm':'as',
        'ava':'av',
        'aym':'ay',
        'aze':'az',
        'bak':'ba',
        'bel':'be',
        'bul':'bg',
        'bih':'bh',
        'bis':'bi',
        'bam':'bm',
        'ben':'bn',
        'bod':'bo',
        'tib':'bo',
        'bre':'br',
        'bos':'bs',
        'cat':'ca',
        'che':'ce',
        'cha':'ch',
        'cos':'co',
        'cre':'cr',
        'ces':'cs',
        'cze':'vs',
        'chu':'cu',
        'chv':'cv',
        'cym':'cy',
        'wel':'cy',
        'dan':'da',
        'deu':'de',
        'ger':'de',
        'div':'dv',
        'dzo':'dz',
        'ewe':'ee',
        'ell':'el',
        'gre':'el',
        'eng':'en',
        'epo':'eo',
        'spa':'es',
        'est':'et',
        'eus':'eu',
        'baq':'eu',
        'fas':'fa',
        'per':'fa',
        'ful':'ff',
        'fin':'fi',
        'fij':'fj',
        'fao':'fo',
        'fra':'fr',
        'fre':'fr',
        'fry':'fy',
        'gle':'ga',
        'gla':'gd',
        'glg':'gl',
        'grn':'gn',
        'guj':'gu',
        'glv':'gv',
        'hau':'ha',
        'heb':'he',
        'hin':'hi',
        'hmo':'ho',
        'hrv':'hr',
        'hat':'ht',
        'hun':'hu',
        'hye':'hy',
        'arm':'hy',
        'her':'hz',
        'ina':'ia',
        'ind':'id',
        'ile':'ie',
        'ibo':'ig',
        'iii':'ii',
        'ipk':'ik',
        'ido':'io',
        'isl':'is',
        'ice':'is',
        'ita':'it',
        'iku':'iu',
        'jpn':'ja',
        'jav':'jv',
        'kat':'ka',
        'geo':'ka',
        'kon':'kg',
        'kik':'ki',
        'kua':'kj',
        'kaz':'kk',
        'kal':'kl',
        'khm':'km',
        'kan':'kn',
        'kor':'ko',
        'kau':'kr',
        'kas':'ks',
        'kur':'ku',
        'kom':'kv',
        'cor':'kw',
        'kir':'ky',
        'lat':'la',
        'ltz':'lb',
        'lug':'lg',
        'lim':'li',
        'lin':'ln',
        'lao':'lo',
        'lit':'lt',
        'lub':'lu',
        'lav':'lv',
        'mlg':'mg',
        'mah':'mh',
        'mri':'mi',
        'mao':'mi',
        'mkd':'mk',
        'mac':'mk',
        'mal':'ml',
        'mon':'mn',
        'mar':'mr',
        'msa':'ms',
        'may':'ms',
        'mlt':'mt',
        'mya':'my',
        'bur':'my',
        'nau':'na',
        'nob':'nb',
        'nde':'nd',
        'nep':'ne',
        'ndo':'ng',
        'nld':'nl',
        'dut':'nl',
        'nno':'nn',
        'nor':'no',
        'nbl':'nr',
        'nav':'nv',
        'nya':'ny',
        'oci':'oc',
        'oji':'oj',
        'orm':'om',
        'ori':'or',
        'oss':'os',
        'pan':'pa',
        'pli':'pi',
        'pol':'pl',
        'pus':'ps',
        'por':'pt',
        'que':'qu',
        'roh':'rm',
        'run':'rn',
        'ron':'ro',
        'rum':'ro',
        'rus':'ru',
        'kin':'rw',
        'san':'sa',
        'srd':'sc',
        'snd':'sd',
        'sme':'se',
        'sag':'sg',
        'sin':'si',
        'slk':'sk',
        'slo':'sk',
        'slv':'sl',
        'smo':'sm',
        'sna':'sn',
        'som':'so',
        'sqi':'sq',
        'alb':'sq',
        'srp':'sr',
        'ssw':'ss',
        'sot':'st',
        'sun':'su',
        'swe':'sv',
        'swa':'sw',
        'tam':'ta',
        'tel':'te',
        'tgk':'tg',
        'tha':'th',
        'tir':'ti',
        'tuk':'tk',
        'tgl':'tl',
        'tsn':'tn',
        'ton':'to',
        'tur':'tr',
        'tso':'ts',
        'tat':'tt',
        'twi':'tw',
        'tah':'ty',
        'uig':'ug',
        'ukr':'uk',
        'urd':'ur',
        'uzb':'uz',
        'ven':'ve',
        'vie':'vi',
        'vol':'vo',
        'wln':'wa',
        'wol':'wo',
        'xho':'xh',
        'yid':'yi', 
        'yor':'yo',
        'zha':'za',
        'zho':'zh',
        'chi':'zh',
        'zul':'zu',
        }
    if marc_code in mapping:
        return mapping[marc_code]
    else:
        return marc_code
        
if __name__ == '__main__':
    sys.stderr.write('I\'m a module.  Don\'t run me directly!')
    sys.exit(-1)
