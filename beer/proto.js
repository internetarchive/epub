var img_template=false;
var pageno=false;

function init()
{
    if (img_template) return img_template;
    var meta_items=document.getElementsByTagName("meta");
    var i=0; var lim=meta_items.length;
    while (i<lim) {
	if (meta_items[i].name==="IMGTEMPLATE") {
	    img_template=meta_items[i].content;
	    break;}
	else i++;}
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
    var start=document.getElementById("abbyyleaf"+n);
    var end=document.getElementById("abbyyleaf"+(n+1));
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
