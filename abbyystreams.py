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

def abbyytext(f, debug=False, header=False, footer=False, picture=False, table=False, format=False,layout=False,pagefn=False,linefn=False,blockfn=False,escapefn=False,floatfn=False):
    passage = ''
    curformat=False
    layoutinfo = False
    pageinfo = False
    leaf_count = 0
    line_count = 0
    thread_break=True
    body_thread=False
    page_width=0
    bottom=0
    for event, page in iterparse(f):
        if page.tag != page_tag: continue
        leaf_count+= 1
        line_count=0
        bottom=0
        if (body_thread):
            yield passage
            passage=body_thread
            body_thread=False
        pageinfo=page.attrib
        if pagefn:
            if layoutinfo:
                layoutinfo=layoutinfo+pagefn(leaf_count,page)
            else: layoutinfo=pagefn(leaf_count,page)
        if debug:
            print 'page', leaf_count, pageinfo
        flow_break = True
        page_width = int(pageinfo["width"])
        for block in page:
            assert block.tag == block_tag
            if blockfn:
               if layoutinfo:
                  layoutinfo=layoutinfo+blockfn(block,leaf_count)
               else: layoutinfo=blockfn(block,leaf_count)
            blockinfo=block.attrib
            if blockinfo['blockType'] == 'Picture':
                flow_break=True
                if (debug):
                    print "Picture" , block.attrib
                if (picture):
                    result,inline=picture(block,leaf_count,pageinfo)
                    if inline:
                       if layoutinfo:
                          layoutinfo=layoutinfo+result
                       else: layoutinfo=result
                    else:
                        if passage != '':
                           if format and curformat:
                              formatted=format(passage,False,curformat)
                              yield formatted
                           else: yield passage
                        passage=''
                        yield result
                continue
            if blockinfo['blockType'] == 'Table':
                flow_break=True
                if (debug):
                    print "Table" , block.attrib
                if (table):
                   result,inline=table(block,leaf_count)
                   if inline:
                      if layoutinfo:
                         layoutinfo=layoutinfo+result
                      else: layoutinfo=result
                   else:
                    if passage != '':
                       if format and curformat:
                          formatted=format(passage,False,curformat)
                          yield formatted
                       else: yield passage
                       passage=''
                       yield result
                continue
            assert blockinfo['blockType'] == 'Text'
            assert len(block) in (1, 2)
            region = block[0]
            assert region.tag == region_tag
            # text = []
            if len(block) == 2:
                e_text = block[1]
                assert e_text.tag == text_tag
            block_width=int(blockinfo["r"])-int(blockinfo["l"])
            if ((int(blockinfo["b"])<bottom) or
                ((block_width<(3*(page_width/4))) and
                 (int(blockinfo["l"])>page_width/10))):
              if (not(body_thread)):
                  body_thread=passage
                  thread_break=flow_break
                  flow_break=True
                  passage=''
            elif (body_thread):
                if (floatfn):
                    result=floatfn(passage)
                else: result=passage
                yield result
                passage=body_thread
                flow_break=thread_break
                body_thread=False
            else: bottom=int(blockinfo["b"])
            if debug:
                if (body_thread):
                    print 'float', block.attrib
                else: print 'block', block.attrib
            for par in e_text:
                assert par.tag == par_tag
                text = ''
                first_lower=False
                first_char=True
                lastr=False
                for line in par:
                    assert line.tag == line_tag
                    line_count+=1
                    if (linefn):
                       result=linefn(line,line_count,leaf_count)
                       if result:
                          if layoutinfo:
                             layoutinfo=layoutinfo+result
                          else: layoutinfo=result
                    if (likelyheader(line,par,e_text,block,page,debug)):
                        if (header):
                            result=header(linecontent(line),line)
                            if not result: continue
                            elif ((type(result)==str) and (result[0]!='\n')):
                                if layoutinfo:
                                   layoutinfo=layoutinfo+result
                                else: layoutinfo=result
                            else:
                                if passage != '':
                                   if format and curformat:
                                      formatted=format(passage,False,curformat)
                                      yield formatted
                                   else: yield passage
                                passage=''
                                yield result
                        continue
                    if (likelyfooter(line,par,e_text,block,page,debug)):
                        if (footer):
                            result=footer(linecontent(line),line)
                            if not result: continue
                            elif ((type(result)==str) and (result[0]!='\n')):
                                 if layoutinfo:
                                    layoutinfo=layoutinfo+result
                                 else:
                                    layoutinfo=result
                            else:
                                if passage != '':
                                   if format and curformat:
                                      formatted=format(passage,False,curformat)
                                      yield formatted
                                   else: yield passage
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
                        if escapefn: cur=escapefn(cur)
                        if format:
                            formatted=format(cur,formatting.attrib,curformat)
                            if formatted:
                                curformat=formatting.attrib
                                cur=formatted
                        text=addtext(text,cur,layoutinfo)
                        layoutinfo=False
                        for charParams in formatting:
                            assert charParams.tag == charParams_tag
                if text == '':
                    continue
                if (passage and first_lower):
                    passage = addtext(passage,text,layoutinfo)
                    layoutinfo=False
                    flow_break = False
                    continue
                if passage:
                   if format and curformat:
                      formatted=format(passage,False,curformat)
                      yield formatted
                   else: yield passage
                passage = text
        if (body_thread):
            yield passage
            passage=body_thread
            body_thread=False
    page.clear()
    if passage:
       if format and curformat:
       	  formatted=format(passage,False,curformat)
	  yield formatted
       else: yield passage

def addtext(passage,text,layout=False):
    if passage=='':
       if layout: return layout+text
       else: return text;
    elif passage[-1]=='-':
        if layout:
	   return passage[:-1]+layout+text
        else: return passage[:-1]+text
    else: return passage+' '+text
        

def likelyheader(line,para,text,block,page,debug):
    pagewidth=int(page.attrib["width"])
    if ((line==para[0]) and (para==text[0]) and
        (block==page[0]) and (len(para) == 1)):
        if (atpagetop(block,page,debug)):
            return (checkoddlyspaced(line,debug,pagewidth))
        elif (atpagetop(block,page,debug,2)):
            return (checkoddlyspaced(line,debug,pagewidth,2))
        else: return False
    else: return False

def likelyfooter(line,para,text,block,page,debug):
    pagewidth=int(page.attrib["width"])
    if ((line==para[-1]) and (para==text[-1]) and
        (block==page[-1]) and (len(para) == 1)):
        if (atpagebottom(block,page,debug)):
            return (checkoddlyspaced(line,debug,pagewidth))
        elif (atpagebottom(block,page,debug,2)):
            return (checkoddlyspaced(line,debug,pagewidth,2))
        else: return False
    else: return False

def checkoddlyspaced(line,debug=False,pagewidth=False,pos=0,thresh=5):
    if (pagewidth):
        la=line.attrib
        linewidth=int(la["r"])-int(la["l"])
        if (linewidth<pagewidth/2): return True
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
        return ((maxspace)>((charwidth/normalchars)*thresh))
    else:
        return ((maxspace)>((maxwidth)*thresh))


def atpagetop(block,page,debug,thresh=1):
    if debug:
        print "t=%d,h=%d,h/10=%d,th=%d"%(int(block.attrib["t"]),int(page.attrib["height"]),int(page.attrib["height"])/10,thresh)
    return (int(block.attrib["t"])<(thresh*(int(page.attrib["height"])/10)))
def atpagebottom(block,page,debug,thresh=1):
    if debug:
        print "b=%d,h=%d,h/10=%d,th=%d"%(int(block.attrib["b"]),int(page.attrib["height"]),int(page.attrib["height"])/10,thresh)
    return (int(block.attrib["b"])>(((10-thresh)*int(page.attrib["height"]))/10))

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

