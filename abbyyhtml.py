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
events=('start','end')

edgethresh=0.1

global_classmap={}

def getblocks(f,book_id="BOOK",classmap=global_classmap):
    leaf_count=1
    block_count=0
    para_count=0
    line_count=0
    leaf_line_count=0
    page_height=-1
    page_width=-1
    for event,node in iterparse(f,events):
        if ((node.tag == page_tag) and (event=='end')):
            node.clear()
            continue
        elif (node.tag == page_tag):
            pageinfo=node.attrib
            page_height=int(pageinfo["height"])
            page_width=int(pageinfo["width"])
            leaf_count=leaf_count+1
            leaf_line_count=1
            yield ("<div class='leafstart' id='abbyleaf%d' data-book='%dx%d'></div>"%
                   (leaf_count,page_width,page_height))
            continue
        elif ((node.tag == block_tag) and (event=='start')):
            blockinfo=node.attrib
            l=int(blockinfo['l'])
            t=int(blockinfo['t'])
            r=int(blockinfo['r'])
            b=int(blockinfo['b'])
            block_count=block_count+1
            yield ("<div class='%s' id='abbyblock%d' data-book='p%d/%dx%d+%d,%d'>"%
                   ((getclassname("block",blockinfo,page_height)),block_count,
                    leaf_count,r-l,b-t,l,t))
            blocktype=blockinfo['blockType']
            if (blocktype=='Text'): continue
            elif (blocktype=='Picture'):
                yield ("<img title='%s/%d[%d,%d,%d,%d]'/>"%
                       (book_id,leaf_count,l,t,r,b))
                continue
            else: continue
        elif ((node.tag == block_tag) and (event=='end')):
            yield "</div>"
            continue
        elif ((node.tag == par_tag) and (event=='end')):
            text=''
            para_l=0
            para_t=0
            para_r=page_width
            para_b=page_height
            para_count=para_count+1
            curfmt=False
            line_no=0
            for line in node:
                lineinfo=line.attrib
                l=int(lineinfo['l'])
                t=int(lineinfo['t'])
                r=int(lineinfo['r'])
                b=int(lineinfo['b'])
                if (l<para_l): para_l=l
                if (r>para_r): para_r=r
                if (t<para_t): para_t=t
                if (b>para_b): para_b=b
                if (text.endswith('- ')):
                    first_char = line[0][0]
                    if (first_char.attrib.get('wordStart') == 'false' or
                        first_char.attrib.get('wordFromDictionary') == 'false'):
                        text=text[:-2]+"<span class='droppedhyphen'></span>"
                line_count=line_count+1
                if (line_no>0):
                    text=text+' '
                    line_no=line_no+1
                else:
                    line_no=1
                leaf_line_count=leaf_line_count+1
                text=text+("<a class='%s' NAME='%sp%dn%d' data-book='p%d/%dx%d+%d,%d' data-baseline='%d'/>"%
                           (getclassname("line",lineinfo,page_height),
                            book_id,leaf_count,leaf_line_count,leaf_count,r-l,b-t,l,t,
                            int(lineinfo['baseline'])))
                for formatting in line:
                    fmt=formatting.attrib
                    classname=getcssname(fmt,curfmt,classmap)
                    if (classname):
                        if (curfmt): text=text+"</span>"
                        text=text+("<span class='%s'>"%classname)
                    text=text+''.join(c.text for c in formatting)
            if (curfmt): text=text+"</span>"
            
            yield ("<p class='%s' id='%s_%d' data-book='%d/%dx%d+%d,%d'>\n%s\n</p>\n"%
                   (getclassname("para",{"l": l,"t": t,"r": r,"b": b},page_height),
                    book_id,para_count,
                    leaf_count,r-l,b-t,l,t,
                    text))
                    
fontmap={}
def getfontname(s):
    if (s in fontmap):
       return fontmap[s]
    else: return "'%s'"%s

def getcssname(format,curformat,classmap):
    if ('%histogram' in classmap):
        classhist=classmap['%histogram']
    else:
        classhist={}
        classmap['%histogram']=classhist
    if ((curformat) and ((not(format)) or (format!=curformat))):
       style=""
       classname=""
       if ("ff" in curformat):
       	  style=style+"font-family: "+getfontname(curformat["ff"])+";"
       if ("fs" in curformat):
       	  style=style+"font-size: "+curformat["fs"][0:-1]+"px;"
       if ("bold" in curformat):
       	  style=style+"font-weight: bold;"
       if ("italic" in curformat):
       	  style=style+"font-style: italic;"
       if style in classmap:
       	  classname=classmap[style]
	  classhist[classname]=classhist[classname]+1
       else:
           if ('%count' in classmap):
               classcount=classmap['%count']
           else:
               classcount=1
           classmap['%count']=classcount+1
           classname="abbyy%d"%classcount
           classmap[style]=classname
           classhist[classname]=1
       return classname
    else: return False

def getclassname(base,attrib,height):
    t=int(attrib['t'])
    b=int(attrib['b'])
    thresh=height*edgethresh
    threshplus=thresh*1.5
    if (b<thresh):
        return base+" pagehead"
    if ((height-t)<thresh):
        return base+" pagefoot"
    return base

