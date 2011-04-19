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

def getblocks(f,book_id="BOOK",classmap=global_classmap,inline_blocks=True):
    leaf_count=-1
    block_count=0
    para_count=0
    line_count=0
    leaf_line_count=0
    page_height=-1
    page_width=-1
    page_top=True
    for event,node in iterparse(f,events):
        if ((node.tag == page_tag) and (event=='end')):
            node.clear()
            continue
        elif ((node.tag == page_tag) and (event=='start')):
            pageinfo=node.attrib
            page_height=int(pageinfo["height"])
            page_width=int(pageinfo["width"])
            leaf_count=leaf_count+1
            leaf_line_count=1
            page_top=True
            yield ("<a class='abbyyleafstart' name='abbyyleaf%d' id='abbyyleaf%d' data-book='%dx%d'>#n%d</a>"%
                   (leaf_count,leaf_count,page_width,page_height,leaf_count))
            continue
        elif ((node.tag == block_tag) and (event=='start')):
            blockinfo=node.attrib
            l=int(blockinfo['l'])
            t=int(blockinfo['t'])
            r=int(blockinfo['r'])
            b=int(blockinfo['b'])
            block_count=block_count+1
            if inline_blocks:
                yield ("<a class='%s' name='abbyyblock%d' data-book='n%d/%dx%d+%d,%d'>#n%db%d</a>"%
                       ((getclassname("abbyyblock",blockinfo,page_width,page_height,page_top)),
                        block_count,leaf_count,r-l,b-t,l,t,leaf_count,block_count))
            else:
                yield ("<div class='%s' id='abbyyblock%d' data-book='n%d/%dx%d+%d,%d'>"%
                       ((getclassname("abbyyblock",blockinfo,page_width,page_height,page_top)),
                        block_count,leaf_count,r-l,b-t,l,t))
            blocktype=blockinfo['blockType']
            if (blocktype=='Text'): continue
            elif (blocktype=='Picture'):
                yield ("<img title='%s/%d[%d,%d,%d,%d]'/>"%
                       (book_id,leaf_count,l,t,r,b))
                continue
            else: continue
        elif ((node.tag == block_tag) and (event=='end')):
            page_top=False
            if inline_blocks:
                continue
            else:
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
            curclass=False
            line_no=0
            for line in node:
                hyphenated=False
                lineinfo=line.attrib
                l=int(lineinfo['l'])
                t=int(lineinfo['t'])
                r=int(lineinfo['r'])
                b=int(lineinfo['b'])
                if (l<para_l): para_l=l
                if (r>para_r): para_r=r
                if (t<para_t): para_t=t
                if (b>para_b): para_b=b
                if (text.endswith('-')):
                    first_char = line[0][0]
                    if (first_char.attrib.get('wordStart') == 'false' or
                        first_char.attrib.get('wordFromDictionary') == 'false'):
                        text=text[:-1]+"<span class='abbyydroppedhyphen'>-</span>"
                        hyphenated=True
                line_count=line_count+1
                if (line_no>0) and (not hyphenated):
                    text=text+' '
                if (line_no>0):
                    line_no=line_no+1
                else:
                    line_no=1
                leaf_line_count=leaf_line_count+1
                lineclass=getclassname("abbyyline",lineinfo,page_width,page_height,page_top)
                anchor=("<a class='%s' NAME='%sn%dl%d' data-book='n%d/%dx%d+%d,%d' data-baseline='%d'"%
                        (lineclass,book_id,
                         leaf_count,leaf_line_count,leaf_count,
                         r-l,b-t,l,t,
                         int(lineinfo['baseline'])))
                closeanchor=""
                if ((lineclass.find("abbyypagehead")>=0) or
                    (lineclass.find("abbyypagefoot")>=0)):
                    if curfmt:
                        text=text+"</span>"+anchor+">"+"<span class='"+curclass+"'>"
                        closeanchor="</span></a>"
                    else:
                        text=text+anchor+">"
                        closeanchor="</a>"
                text=text+("<span class='abbyylineinfo'>#n%dl%d</span>"%(leaf_count,line_count))
                for formatting in line:
                    fmt=formatting.attrib
                    classname=getcssname(fmt,curfmt,classmap)
                    if (classname):
                        curfmt=fmt
                        curclass=classname
                    if (classname):
                        if (curfmt): text=text+"</span>"
                        text=text+("<span class='%s'>"%classname)
                    text=text+''.join(c.text for c in formatting)
                text=text+closeanchor
            if (curfmt): text=text+"</span>"
            
            classname=getclassname("abbyypara",{"l": l,"t": t,"r": r,"b": b},
                                   page_width,page_height,page_top)
            if ((classname.find("abbyypagehead")>=0) or
                (classname.find("abbyypagefoot")>=0)):
                tagname="span"
                newline=""
            else:
                tagname="p"
                newline="\n"
            stripped=text.strip()
            if len(stripped) > 0:
                yield ("<%s class='%s' id='%s_%d' data-book='%d/%dx%d+%d,%d'>%s</%s>%s"%
                       (tagname,classname,
                        book_id,para_count,
                        leaf_count,r-l,b-t,l,t,
                        stripped,tagname,newline))
            curfmt=False
            curclass=False
                    
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

def getclassname(base,attrib,width,height,pagetop):
    t=int(attrib['t'])
    b=int(attrib['b'])
    l=int(attrib['l'])
    r=int(attrib['r'])
    thresh=height*edgethresh
    if pagetop:
        thresh=thresh*0.75
    if (b<thresh):
        return base+" abbyypagehead"
    elif ((height-t)<thresh):
        return base+" abbyypagefoot"
    elif ((height-b)<(thresh/2)):
        return base+" abbyypagefoot"
    elif (((r-l)<(width*0.8)) and (l>(width*0.2))):
        return base+" abbyycentered"
    return base

        
