#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re

from datetime import datetime
from debug import debug, debugging

import sys

from lxml import etree

def tree_to_str(tree, xml_declaration=True):
    return etree.tostring(tree,
                          pretty_print=True,
                          xml_declaration=xml_declaration,
                          encoding='utf-8')


def get_metadata_tag_data(metadata, tag):
    for el in metadata:
        if el['tag'] == tag:
            return el['text']
    return 'Unknown'


def get_dt_str():
    dt = datetime.now()
    return (str(dt.year) + str(dt.month) + str(dt.day) +
            str(dt.hour) + str(dt.minute) + str(dt.second))


def recursive_dict(element):
    return element.tag, dict(map(recursive_dict, element)) or element.text


rnums = {
    'i':1, 'ii':2, 'iii':3, 'iv':4, 'v':5,
    'vi':6, 'vii':7, 'viii':8, 'ix':9, 'x':10,
    'xi':11, 'xii':12, 'xiii':13, 'xiv':14, 'xv':15,
    'xvi':16, 'xvii':17, 'xviii':18, 'xix':19, 'xx':10,
    'xxi':21, 'xxii':22, 'xxiii':23, 'xxiv':24, 'xxv':25,
    'xxvi':26, 'xxvii':27, 'xxviii':28, 'xxix':29, 'xxx':30,
    'xxxi': 31, 'xxxii': 32, 'xxxiii': 33, 'xxxiv':34, 'xxxv':35,
    'xxxvi':36, 'xxxvii':37, 'xxxviii':38, 'xxxix':39, 'xl':40,
    'xli':41, 'xlii':42, 'xliii':43, 'xliv':44, 'xlv':45,
    'xlvi':46, 'xlvii':47, 'xlviii':48, 'xlix':49, 'l':50,
    'li':51, 'lii':52, 'liii':53, 'liv':54, 'lv':55,
    'lvi':56, 'lvii':57, 'lviii':58, 'lix':59, 'lx':60,
    'lxi':61, 'lxii':62, 'lxiii':63, 'lxiv':64, 'lxv':65,
    'lxvi':66, 'lxvii':67, 'lxviii':68, 'lxix':69, 'lxx':70,
    # lxx lccc
    }
def rnum_to_int(r):
    r = r.lower()
    if r in rnums:
        return rnums[r]
    return 0
    


def p_el(el, maxdepth=2, curdepth=0, prefix=''):
    result = prefix
    result += el.tag
    if el.text is not None:
        result += ' ' + el.text
    result += '\n'
    if curdepth > maxdepth:
        return result
    for kid_el in el.iterchildren():
        result += prefix + p_el(kid_el, maxdepth, curdepth + 1, prefix + '  ')
    return result


def par_is_pageno_header_footer(par):
    result = db_par_hdr_ftr(par)
    if result and debugging:
        line_text = etree.tostring(par,
                                   method='text',
                                   encoding='utf-8')
        print line_text.strip()
    return result

def db_par_hdr_ftr(par):
    if len(par) != 1:
        return False
    line = par[0]
    line_text = etree.tostring(line,
                               method='text',
                               encoding=unicode)
    line_text = line_text.lower()
    if re.match('[\[li] *[0-9afhiklmnouvx^]*[0-9][0-9afhiklmnouvx^]* *[\]ijl1]',
                line_text):
        return True
    if re.match('[\[li] *[xiv]* *[\]ijl1]',
                line_text):
        return True
    for fmt in line:
        if len(fmt) > 6:
            continue
        if float(fmt.get('fs')) > 40:
            continue
        fmt_text = etree.tostring(fmt,
                              method='text',
                              encoding=unicode)
        fmt_text = fmt_text.lower()
        if rnum_to_int(fmt_text) > 0:
            return True
        # common OCR errors
        if re.match('[0-9io]+', fmt_text):
            return True
        if re.match('[0-9afhiklmnouvx^]*[0-9][0-9afhiklmnouvx^]*',
                    fmt_text):
            return True
    return False

if __name__ == '__main__':
    sys.stderr.write("I'm a module.  Don't run me directly!")
    sys.exit(-1)
