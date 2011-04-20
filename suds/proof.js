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
  var lineinfo=copy_array(document.getElementsByClassName("abbyylineinfo"));
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
var editor=false;
var edit_list=[];
var change_count=0;

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
  editor.value=word.innerHTML;
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
  var replacement=editing.cloneNode(true);
  var now=Date().toString();
  edit_record={before:editing.innerHTML,
	       after:new_content,
	       abbyy: editing.getAttribute("data-abbyy"),
	       olib: olib,
	       user:"somebody",
	       date:now};
  edit_list.push(edit_record);
  replacement.innerHTML=new_content;
  replacement.className=replacement.className
  editing.parentNode.insertBefore(replacement,editing);
  editing.className=editing.className.replace(/ editing$/," replaced");
  replacement.className=replacement.className.replace(/ editing$/," edited");
  editing.parentNode.removeChild(editor);
  editing=false;
  editor=false;
}

function cancel_edit()
{
  editing.className=editing.className.replace(/ editing$/,"");
  editing.parentNode.removeChild(editor);
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

