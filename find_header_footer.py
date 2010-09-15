import re
from lxml import etree

ns = '{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}'

def hf_candidates(page):
    result = []
    lines = [line for line in page.findall('.//'+ns+'line')]
    hfwin = 5
    for i in range(hfwin) + range(-hfwin, 0):
        if abs(i) < len(lines):
            result.append((lines[i], simplify_line_text(lines[i])))
        else:
            result.append(None)
    return result

def simplify_line_text(line):
    text = etree.tostring(line,
                          method='text',
                          encoding=unicode).lower();
    # collape numbers (roman too) to '@' so headers will be more
    # similar from page to page
    return re.sub(r'[ivx\d]', r'@', text)

def guess_hf(pageinfo, pages):
    hf_candidates = pageinfo.info['hf_candidates']
    pass

