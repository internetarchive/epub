<?php

$olib_arg=$_GET['OLIB'];
$leaf_arg=$_GET['LEAF'];

$contentType = 'text/html'; // default

header('Content-type: ' . $contentType . ';charset=UTF-8');
header('Access-Control-Allow-Origin: *'); // allow cross-origin requests

if ((!($olib_arg))||(len($olib_arg))) $olib_arg="OL2588416M";
if ((!($leaf_arg))||(len($leaf_arg))) $leaf_arg="42";
					

$olib = escapeshellarg($olib_arg);
$leaf = escapeshellarg($leaf_arg);

set_time_limit(120);
passthru("python proto.py $olib $leaf 2>&1");
?>