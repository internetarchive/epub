<?php

$bookid=$_REQUEST['BOOKID'];
$olid=$_REQUEST['OLID'];
$content=$_REQUEST['CONTENT'];

$contentType = 'text/html'; // default

header('Content-type: ' . $contentType . ';charset=UTF-8');
header('Access-Control-Allow-Origin: *'); // allow cross-origin requests

set_time_limit(240);

$cache_file="./cache/" . $bookid . ".html";
$stream=fopen($cache_file,"w");
fwrite($stream,$content);
fclose($stream);

passthru("python ../corrected.py $olid $bookid $cache_file 2>&1");
?>
