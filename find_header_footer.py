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



# def rearrange_lines(page):
#     lb = line_builder()
#     findexpr = './/'+ns+'line'
#     for line in page.findall(findexpr):
#         lb.add(line)
#     print len(lb.linerecs)
#     # lb.linerecs.clear()

# def range_compare(r1, r2):
#     t1, b1 = r1
#     t2, b2 = r2
#     if b1 < t2:
#         return -1
#     if b2 < t1:
#         return 1
#     return 0

# def range_union(r1, r2):
#     t1, b1 = r1
#     t2, b2 = r2
#     t = t1 if t1 < t2 else t2
#     b = b1 if b1 > b2 else b2
#     return (t, b)
        
# # shelved for now - not needed for non-col books?
# class line_builder:
#     def __init__(self):
#         self.linerecs = []
#     def add(self, el):
#         for lineno, linerec in enumerate(self.linerecs):
#             c = range_compare(tbrange(el),
#                                linerec['range'])
#             if c == -1:
#                 linerecs.insert(lineno, { 'range':tbrange(el),
#                                        'els':[el] })
#                 return
#             if c == 0:
#                 linerec['range'] = range_union(linerec['range'],
#                                                tbrange(el))
#                 linerec['els'].append(el)
#                 print 'combined'
#                 return
#             # still here
#             linerecs.append({ 'range': tbrange(el),
#                               'els':[el] })
            
# def tbrange(el):
#     return (t(el), b(el))

# def t(el):
#     return int(el.attrib['t'])

# def b(el):
#     return int(el.attrib['b'])
