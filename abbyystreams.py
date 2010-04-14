from lxml.etree import iterparse, tostring
import re

ns = '{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}'
page_tag = ns + 'page'
block_tag = ns + 'block'
region_tag = ns + 'region'
text_tag = ns + 'text'
rect_tag = ns + 'rect'
par_tag = ns + 'par'
line_tag = ns + 'line'
formatting_tag = ns + 'formatting'
charParams_tag = ns + 'charParams'

re_page_num = re.compile(r'^\[?\d+\]?$')

def abbyytext(f, debug=False, header=False, footer=False, picture=False, table=False, format=False):
    passage = ''
    curformat=False
    page_count = 0
    for event, element in iterparse(f):
        if element.tag == page_tag:
            page_count+= 1
            if debug:
                print 'page', page_count
            page_break = True
            for block in element:
                assert block.tag == block_tag
                if block.attrib['blockType'] == 'Picture':
                    if (picture):
                        result=picture(block)
                        if not result: continue
                        elif ((typeof(result)==str) and
                              (result[0]!='\n')):
                            passage=addtext(passage,result,True)
                        else:
                            if passage != '': yield passage
                            passage=''
                            yield result
                    continue
                if block.attrib['blockType'] == 'Table':
                    if (table):
                        result=table(block)
                        if not result: continue
                        elif ((typeof(result)==str) and
                              (result[0]!='\n')):
                            passage=addtext(passage,result,True)
                        else:
                            if passage != '': yield passage
                            passage=''
                            yield result
                    continue
                assert block.attrib['blockType'] == 'Text'
                assert len(block) in (1, 2)
                region = block[0]
                assert region.tag == region_tag
                # text = []
                if len(block) == 2:
                    e_text = block[1]
                    assert e_text.tag == text_tag
                if debug:
                    print 'block', block.attrib
                for par in e_text:
                    assert par.tag == par_tag
                    text = ''
                    first_lower=False
                    first_char=True
                    lastr=False
                    for line in par:
                        assert line.tag == line_tag
                        if ((line==par[0]) and (par==e_text[0]) and (block==element[0]) and
                            (atpagetop(block,element,debug)) and
                            (len(par) == 1) and
                            (checkoddlyspaced(line,0,debug))):
                            if (header):
                                result=header(linecontent(line),line)
                                if not result: continue
                                elif ((typeof(result)==str) and (result[0]!='\n')):
                                    passage=addtext(passage,result,True)
                                else:
                                    if passage != '': yield passage
                                    passage=''
                                    yield result
                            continue
                        if ((line==par[-1]) and (par==e_text[-1]) and (block==element[-1]) and
                            (atpagebottom(block,element,debug)) and
                            len(par) == 1 and
                            (checkoddlyspaced(line,0,debug))):
                            if (footer):
                                result=footer(linecontent(line),line)
                                if not result: continue
                                elif ((typeof(result)==str) and (result[0]!='\n')):
                                    passage=addtext(passage,result,True)
                                else:
                                    if passage != '': yield passage
                                    passage=''
                                    yield result
                            continue
                        for formatting in line:
                            assert formatting.tag == formatting_tag
                            cur = ''.join(e.text for e in formatting)
                            if cur=='': continue
                            elif first_char:
                                first_char=False
                                if cur[0].islower(): first_lower=True
                            if format:
                                formatted=format(cur,formatting.attrib,curformat)
                                if formatted:
                                    curformat=formatting.attrib
                                    cur=formatted
                            text=addtext(text,cur)
                            for charParams in formatting:
                                assert charParams.tag == charParams_tag
                    if text == '':
                        continue
                    if page_break:
                        if (passage and first_lower):
                            passage = addtext(passage,text)
                            page_break = False
                            continue
                        page_break = False
                    if passage:
                        yield passage
                    passage = text

            element.clear()
    if passage:
        yield passage

def addtext(passage,text,extra=False):
    if passage=='': return text
    elif passage[-1]=='-':
        if extra:
            point=passage.rfind(' ')
            if point:
                return passage[:point]+' '+text+' '+passage[point:-1]
            else: return passage[:-1]
        else:
            return passage[:-1]+text
    else: return passage+' '+text
        

def checkoddlyspaced(line,pos=0,debug=False):
    charwidth=0
    charspace=0
    nchars=0
    normalchars=0
    maxspace=0
    maxwidth=0
    text=False
    if (debug):
        text=''
    for fmt in line:
        assert fmt.tag == formatting_tag
        for charp in fmt:
            assert charp.tag == charParams_tag
            space=int(charp.attrib['l'])-pos
            pos=int(charp.attrib['r'])
            width=pos-int(charp.attrib['l'])
            if (('wordNormal' not in charp.attrib or not((charp.attrib["wordNormal"]=="true"))) or (charp.attrib["wordNumeric"]=="true")):
                space=space+width
                width=0
            else:
                normalchars=normalchars+1
            if (space>maxspace):
                maxspace=space
            if (width>maxwidth):
                maxwidth=width
            charspace=charspace+space
            charwidth=charwidth+width
            nchars=nchars+1
            if (text):
                text=text+charp.text
    if (debug):
        print "headfoot tspace=%d twidth=%d mspace=%d mwidth=%d norm=%d n=%d/%s"%\
              (charspace,charwidth,maxspace,maxwidth,normalchars,nchars,text)
    if (normalchars>0):
        return ((maxspace)>((charwidth/normalchars)*5))
    else:
        return ((maxspace)>((maxwidth)*5))


def atpagetop(block,page,debug):
    if debug:
        print "t=%d,h=%d,h/10=%d"%(int(block.attrib["t"]),int(page.attrib["height"]),int(page.attrib["height"])/10)
    return (int(block.attrib["t"])<(int(page.attrib["height"])/10))
def atpagebottom(block,page,debug):
    if debug:
        print "b=%d,h=%d,h/10=%d"%(int(block.attrib["b"]),int(page.attrib["height"]),int(page.attrib["height"])/10)
    return (int(block.attrib["b"])>((9*int(page.attrib["height"]))/10))
def linecontent(line):
    text=''
    for fmt in line:
        for charp in fmt:
            text=text+charp.text
    return text
def closenough(lastr,lastbutr):
    if ((lastr) and (lastbutr)):
        return ((5*(lastbutr-lastr))<lastbutr)
    else: return False


def oob_trace(kind,string,data):
    print "%s:%s"%(kind,string)


