<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');

$input = json_decode(file_get_contents('php://input'), true) ?? [];
define('DATA_DIR', __DIR__ . '/../data');
if (!is_dir(DATA_DIR)) mkdir(DATA_DIR, 0755, true);

function saveJson($f, $d) { file_put_contents(DATA_DIR.'/'.$f, json_encode($d, JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT)); }
function loadJson($f) { $p = DATA_DIR.'/'.$f; return file_exists($p) ? json_decode(file_get_contents($p), true) : []; }

$type = $_GET['type'] ?? '';

if ($type === 'load') {
    echo json_encode([
        'routes' => loadJson('routes.json'),
        'services' => loadJson('services.json'),
        'categories' => loadJson('categories.json'),
        'requests' => loadJson('requests.json')
    ], JSON_UNESCAPED_UNICODE);
} elseif ($type === 'routes') {
    saveJson('routes.json', $input);
    echo json_encode(['success' => true]);
} elseif ($type === 'services') {
    saveJson('services.json', $input);
    echo json_encode(['success' => true]);
} elseif ($type === 'categories') {
    saveJson('categories.json', $input);
    echo json_encode(['success' => true]);
} elseif ($type === 'requests') {
    saveJson('requests.json', $input);
    echo json_encode(['success' => true]);
} elseif ($type === 'ping') {
    echo json_encode(['status' => 'ok', 'time' => date('Y-m-d H:i:s')]);
} else {
    echo json_encode(['error' => 'Unknown type']);
}