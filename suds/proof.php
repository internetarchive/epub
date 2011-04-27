<?php

$olib_arg=$_REQUEST['OLIB'];
$leaf_arg=$_REQUEST['LEAF'];

$contentType = 'text/html'; // default

header('Content-type: ' . $contentType . ';charset=UTF-8');
header('Access-Control-Allow-Origin: *'); // allow cross-origin requests

if ((!($olib_arg))||(strlen($olib_arg)==0)) $olib_arg="OL2588416M";
if ((!($leaf_arg))||(strlen($leaf_arg)==0)) $leaf_arg="42";

$olib = escapeshellarg($olib_arg);
$leaf = escapeshellarg($leaf_arg);

set_time_limit(120);
passthru("python ../correctform.py $olib $leaf 2>&1");
?>