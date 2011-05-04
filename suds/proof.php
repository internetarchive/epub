<?php

$spec_arg=$_REQUEST['SPEC'];
$leaf_arg=$_REQUEST['LEAF'];

$contentType = 'text/html'; // default

header('Content-type: ' . $contentType . ';charset=UTF-8');
header('Access-Control-Allow-Origin: *'); // allow cross-origin requests

if ((!($spec_arg))||(strlen($spec_arg)==0)) $spec_arg="handofethelberta01hard";
if ((!($leaf_arg))||(strlen($leaf_arg)==0)) $leaf_arg="42";

$spec = escapeshellarg($spec_arg);
$leaf = escapeshellarg($leaf_arg);

set_time_limit(720);
passthru("python ../correctform.py $spec $leaf ./cache/ 2>&1");
?>