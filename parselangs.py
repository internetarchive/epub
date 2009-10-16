#!/usr/bin/python
# -*- coding: utf-8 -*-
from debug import debug, debugging, assert_d

import json

from lxml import html
#from lxml.html import soupparser as s
from lxml import etree

t = html.parse('langs.htm')
table = t.getroot()[1][0]

result = {}

iso639_2_T = {}
iso639_2_B = {}
iso639_3 = {}
lang_name = {}
native_name = {}

first = True
for row in table:
    if first:
        first = False
        continue
    abbrev = row[0].text
    iso639_2_T[row[1].text] = abbrev
    if row[2].text != u'-':
        iso639_2_B[row[2].text] = abbrev
    if row[3].text != u'—' and row[3].text != u'-':
        iso639_3[row[3].text[:3]] = abbrev
    if len(row[4]) > 0:
        coltext = etree.tostring(row[4], method='text', encoding=unicode)
        for name in coltext[:-1].split(', '):
            lang_name[name.lower()] = abbrev
    if row[5].text is not None:
        for name in row[5].text.split(', '):
            native_name[name.lower()] = abbrev

print 'mapping = ' + json.dumps([iso639_2_T,
                                 iso639_2_B,
                                 iso639_3,
                                 lang_name,
                                 native_name], sort_keys=True, indent=4)
