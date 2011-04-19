var img_template=false;
var pageno=false;

function init()
{
  pagetext=document.getElementById("PAGETEXT");
  if (img_template) return img_template;
  var meta_items=document.getElementsByTagName("meta");
  var i=0; var lim=meta_items.length;
  while (i<lim) {
    if (meta_items[i].name==="IMGTEMPLATE") {
      img_template=meta_items[i].content;
      break;}
    else i++;}
  var lineinfo=document.getElementsByClassName("abbyylineinfo");
  if (lineinfo) {
    var i=0; var lim=lineinfo.length;
    while (i<lim) {
      var info=lineinfo[i++];
      var newbreak=document.createElement("BR");
      newbreak.className="abbyybreak";
      info.parentNode.insertBefore(newbreak,info);}}
  return img_template;
}

function gotoPage(n)
{
    if (!(n)) n=pageno;
    if (!(n)) n=parseInt(document.body.getAttribute("data-startpage"));
    var pagestring=n.toString();
    while (pagestring.length<4) pagestring="0"+pagestring;
    var img_elt=document.getElementById("PAGEIMAGE");
    img_elt.src=img_template.replace("%%%%",pagestring);
    var found=document.getElementsByClassName("displayed");
    var current=[]
    var i=0; var lim=found.length;
    while (i<lim) {current[i]=found[i]; i++;}
    i=0; while (i<lim) {
	var node=current[i++];
	node.className=node.className.replace(/\bdisplayed\b/g,"").trim();}
    var leaf_start=document.getElementById("abbyyleaf"+n);
    var start=leaf_start;
    var leaf_end=document.getElementById("abbyyleaf"+(n+1));
    var end=leaf_end;
    var textbox=document.getElementById("PAGETEXT");
    while (start) {
	if (start.parentNode===textbox) break;
	else start=start.parentNode;}
    while (end) {
	if (end.parentNode===textbox) break;
	else end=end.parentNode;}
    var scan=start;
    while ((scan)&&(scan!==end)) {
	if (scan.nodeType===1)
	    scan.className=scan.className+" displayed";
	scan=scan.nextSibling;}
    if ((scan)&&(scan.nodeType===1))
	scan.className=scan.className+" displayed";
    pageno=n;
    var dispelt=document.getElementById("PAGEDISPLAY");
    dispelt.innerHTML=(n).toString();
    var inputelt=document.getElementById("PAGEINPUT");
    inputelt.value=(n).toString();
    markoffpage(leaf_start,leaf_end);
}

function copy_array(array)
{
  var copy=[];
  var i=0; var lim=array.length;
  while (i<lim) copy.push(array[i++]);
  return copy;
}

var pagetext;

function markoffpage(start,end)
{
  var cleanup=copy_array(document.getElementsByClassName("offpage"));
  var i=0; var lim=cleanup.length;
  while (i<lim) {
    var span=cleanup[i++];
    var parent=span.parentNode;
    var children=copy_array(span.childNodes);
    var j=0; var jlim=children.length;
    while (j<jlim) {
      var child=children[j++];
      parent.insertBefore(child,span);}
    parent.removeChild(span);}
  markbeforepage(start);
  markafterpage(end);
}

function markbeforepage(start)
{
  if (start.parentNode===pagetext) return;
  else {
    var parent=start.parentNode;
    var offpage=document.createElement("span");
    offpage.className="offpage";
    var children=copy_array(parent.childNodes);
    var i=0; var lim=children.length;
    while (i<lim)
      if (children[i]===start) break;
      else offpage.appendChild(children[i++]);
    parent.insertBefore(offpage,start);
    markbeforepage(parent);}
}

function markafterpage(end)
{
  if (end.parentNode===pagetext) return;
  else {
    var parent=end.parentNode;
    var offpage=document.createElement("span");
    offpage.className="offpage";
    var children=copy_array(parent.childNodes);
    var i=0; var lim=children.length; var hide=false;
    while (i<lim) {
      if (hide) offpage.appendChild(children[i]);
      else if (children[i]===end) hide=true;
      else {}
      i++;}
    parent.appendChild(offpage);
    markafterpage(parent);}
}


function toggleClass(elt,classname)
{
    var rx=new RegExp("\\b"+classname+"\\b","g");
    var current=elt.className;
    if (!(current))
	elt.className=classname;
    else if (current===classname)
	elt.className=null;
    else if ((current)&&(current.search(rx)>=0))
	elt.className=current.replace(rx,"").replace(/\s+/," ").trim();
    else if (current)
	elt.className=current+" "+classname;
    else elt.className=classname;
}

function leaf_keypress(evt)
{
    evt=evt||event;
    if (evt.charCode===13) {
	var leafinput=document.getElementById("PAGEINPUT");
	gotoPage(parseInt(leafinput.value));
	if (evt.preventDefault) evt.preventDefault();
	else evt.returnValue=false;
	evt.cancelBubble=true;
	return false;}
}

