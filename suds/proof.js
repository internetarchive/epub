/* -*- Mode: javascript; -*- */

var img_template=false;
var pageno=false;

function copy_array(array)
{
    var copy=[];
    var i=0; var lim=array.length;
    while (i<lim) copy.push(array[i++]);
    return copy;
}

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
    return img_template;
}

function gotoPage(n)
{
    if (!(n)) n=pageno;
    if (!(n)) n=parseInt(document.body.getAttribute("data-startpage"));
    var pagestring=n.toString();
    var img_elt=document.getElementById("PAGEIMAGE");
    img_elt.src=img_template.replace("%",pagestring);
    var current=copy_array(document.getElementsByClassName("displayed"));
    var i=0; var lim=current.length;
    i=0; while (i<lim) {
	var node=current[i++];
	node.className=node.className.replace(/\bdisplayed\b/,"")
	    .replace(/\s+/," ").trim();}
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

function dropClass(elt,classname)
{
    var rx=new RegExp("\\b"+classname+"\\b","g");
    var current=elt.className;
    if (!(current)) return;
    else if (current===classname) {
	elt.className=null;
	return;}
    else if ((current)&&(current.search(rx)>=0)) {
	elt.className=current.replace(rx,"").replace(/\s+/," ").trim();
	return;}
    else return;
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

var editing=false;
var extended=[];
var editor=false;
var edit_list=[];
var change_count=0;

function getNextElement(node)
{
    node=node.nextSibling;
    while (node) {
	if (node.nodeType===1) return node;
	else node=node.nextSibling;}
    return node;
}

function extend_edit(word)
{
    var next=getNextElement(word);
    if ((editing)&&(next===editing)) {
	// It's before the current span
	var before=[]; var prefix=word.innerHTML;
	var scan=word.nextSibling;
	while ((scan)&&(scan!==editing)) {
	    if (scan.nodeType===3) prefix=prefix+scan.nodeValue;
	    before.push(scan);
	    scan=scan.nextSibling;}
	extended=before.concat(extended);
	editing=word;
	editor.value=prefix+editor.value;}
    else if ((editing)&&
	     (((extended.length===0)&&
	       (word===getNextElement(editing)))||
	      ((extended.length)&&
	       (word===getNextElement(extended[extended.length-1]))))) {
	// There's no span and it's after the current word
	var postfix="";
	var last=((extended.length)?(extended[extended.length-1]):(editing));
	var scan=last.nextSibling;
	while ((scan)&&(scan!==word)) {
	    extended.push(scan);
	    if (scan.nodeType===3) postfix=postfix+scan.nodeValue;
	    scan=scan.nextSibling;}
	postfix=postfix+word.innerHTML;
	extended.push(word);
	editor.value=editor.value+postfix;}
    else {
	alert("Multiple words need to be contiguous and on the same line.");
	return false;}
    /* We've added it, so we change the class to editing and return true. */
    if (word.className.search(/\bediting\b/)<0)
	word.className=word.className+" editing";
    return true;
}

function editword_click(evt)
{
    evt=evt||event;
    var word=evt.target||evt.srcElement;
    while (word) {
	if ((word)&&(word.className)&&
	    (word.className.search(/\babbyyword\b/)>=0))
	    break;
	else word=word.parentNode;}
    if (!(word)) return;
    if (word===editing) {
	cancel_edit();
	return;}
    else if ((editing)&&(evt.shiftKey)) {
	extend_edit(word);
	editor.selectionStart=0;
	editor.selectionEnd=editor.value.length;
	return;}
    // If we're editing another word, we finish it up
    else if (editing) save_edit();
    var parent=word.parentNode;
    var uuid=word.getAttribute("data-uuid");
    var editno=word.getAttribute("data-revision");
    if (editno) editno=parseInt(editno)+1;
    else editno=1;
    if (word.className.search(/\bediting\b/)<0)
	word.className=word.className+" editing";
    editor=document.createElement("INPUT");
    editor.type="TEXT";
    editor.setAttribute("SPELLCHECK","true");
    editor.className='wordeditor';
    editor.defaultValue=editor.value=word.innerHTML;
    editor.onkeydown=editor_keydown;
    parent.insertBefore(editor,word);
    editor.selectionStart=0;
    editor.selectionEnd=editor.value.length;  
    editor.focus();
    editing=word;
    change_count++;
}

function save_edit()
{
    var new_content=editor.value;
    editing.parentNode.removeChild(editor);
    if (new_content!==editor.defaultValue) {
	var replacement=editing.cloneNode(true);
	var now=Date().toString();
	var before=editing.innerHTML;
	var abbyy=[editing.getAttribute("data-abbyy")];
	var new_abbyy=abbyy[0];
	if ((extended)&&(extended.length)) {
	    new_abbyy=editing.getAttribute("data-abbyy");
	    var i=0; var lim=extended.length;
	    while (i<lim) {
		var node=extended[i++];
		if (node.nodeType===1) {
		    if (node.getAttribute("data-abbyy")) {
			new_abbyy=mergeAbbyyHTML(node.getAttribute("data-abbyy"),new_abbyy);
			abbyy.push(node.getAttribute("data-abbyy"));}
		    before=before+node.innerHTML;}
		else if (node.nodeType===1)
		    before=before+node.nodeValue;}}
	var scan=editing;
	while (scan) {
	  if (scan.id) break;
	  else scan=scan.parentNode;}
	edit_record={before:before,
		     after:new_content,
		     abbyy: abbyy,
		     new_abbyy: new_abbyy,
		     olib: olib,
		     user:"somebody",
		     date:now};
	if (scan) edit_record.passage=scan.id
	edit_list.push(edit_record);
	replacement.innerHTML=new_content;
	editing.parentNode.insertBefore(replacement,editing);
	if ((extended)&&(extended.length)) {
	    replacement.setAttribute("data-abbyy",new_abbyy);
	    var wrapper=document.createElement("span");
	    wrapper.className="replaced";
	    editing.className=editing.className.replace(/ editing$/," replaced");
	    wrapper.appendChild(editing);
	    var i=0; var lim=extended.length;
	    while (i<lim) {
		var replaced=extended[i++];
		wrapper.appendChild(replaced);
		if (replaced.nodeType===1) {
		    replaced.className=replaced.className.replace(/ editing$/," replaced");}}
	    if (replacement.nextSibling)
		replacement.parentNode.insertBefore(wrapper,replacement.nextSibling);
	    else replacement.parentNode.appendChild(wrapper);}
	else editing.className=editing.className.replace(/ editing$/," replaced");
	replacement.className=replacement.className.replace(/ editing$/," edited");
	dropClass(replacement,"abbyyweird");
	dropClass(replacement,"abbyyunknown");}
    editing=false;
    extended=[];
    editor=false;
}

var abbyyword_rx=/n(\d+)\/i(\d+)\/(\d+)x(\d+)\+(\d+),(\d+)/;

function parseAbbyyHTML(string)
{
    var match=string.match(abbyyword_rx);
    if (!(match)) return false;
    var n=parseInt(match[1]);
    var i=parseInt(match[2]);
    var w=parseInt(match[3]);
    var h=parseInt(match[4]);
    var l=parseInt(match[5]);
    var t=parseInt(match[6]);
    return {n: n,i: i,w: w,h: h,l: l,t: t,r: l+w,b: t+h};
}

function mergeAbbyyHTML(v1,v2)
{
    var p1=parseAbbyyHTML(v1);
    var p2=parseAbbyyHTML(v2);
    var l=((p1.l<p2.l)?(p1.l):(p2.l));
    var t=((p1.t<p2.t)?(p1.t):(p2.t));
    var r=((p1.r>p2.r)?(p1.r):(p2.r));
    var b=((p1.b>p2.b)?(p1.b):(p2.b));
    return "n"+p1.n+"/i"+p1.i+"/"+(r-l)+"x"+(b-t)+"/"+l+","+t;;
}

function cancel_edit()
{
    editing.className=editing.className.replace(/ editing$/,"").replace(/\s+/," ").trim();
    editing.parentNode.removeChild(editor);
    if ((extended)&&(extended.length)) {
	var i=0; var lim=extended.length;
	while (i<lim) {
	    var word=extended[i++];
	    word.className=word.className.replace(/ editing$/,"").replace(/\s+/," ").trim();}
	extended=false;}
    editing=false;
    editor=false;
}

function editor_keydown(evt)
{
    evt=evt||event;
    var kc=evt.keyCode;
    if (!(editing)) return;
    if (kc===13) {
	save_edit();
	if (evt.preventDefault) evt.preventDefault();
	else evt.returnValue=false;
	evt.cancelBubble=true;}
}

function onsave_submit(evt)
{
  evt=evt||event;
  var textcell=document.getElementById("PAGETEXT");
  var content=textcell.innerHTML;
  var style=document.getElementById('ABBYYSTYLE');
  var content_elt=document.getElementById("SAVECONTENT");
  var doc="<html>\n<head>/\n<style>\n"+
    style.innerText+"\n</style>\n</head><body class='abbyytext'>"+
    content+"</body>\n"
  content_elt.value=doc;
}

