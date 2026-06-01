<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');

$input = json_decode(file_get_contents('php://input'), true) ?? [];
define('DATA_DIR', __DIR__ . '/../data');

if (!is_dir(DATA_DIR)) mkdir(DATA_DIR, 0755, true);

function saveData($f, $d) { 
    file_put_contents(DATA_DIR.'/'.$f, json_encode($d, JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT)); 
}
function loadData($f) { 
    $p = DATA_DIR.'/'.$f; 
    return file_exists($p) ? json_decode(file_get_contents($p), true) : null; 
}

$p = $_GET['path'] ?? '';
$m = $_SERVER['REQUEST_METHOD'];

if ($p === 'routes') {
    if ($m === 'GET') echo json_encode(loadData('routes.json') ?? [], JSON_UNESCAPED_UNICODE);
    elseif ($m === 'POST' && isset($input['action'])) {
        $c = loadData('routes.json') ?? [];
        if ($input['action'] === 'save') {
            if (isset($input['routeSettings'])) $c['routeSettings'] = $input['routeSettings'];
            if (isset($input['customRoutes'])) $c['customRoutes'] = $input['customRoutes'];
        }
        saveData('routes.json', $c);
        echo json_encode(['success' => true]);
    }
} elseif ($p === 'services') {
    if ($m === 'GET') echo json_encode(loadData('services.json') ?? [], JSON_UNESCAPED_UNICODE);
    elseif ($m === 'POST' && isset($input['action']) && $input['action'] === 'save') {
        saveData('services.json', $input['services'] ?? []);
        echo json_encode(['success' => true]);
    }
} elseif ($p === 'categories') {
    if ($m === 'GET') echo json_encode(loadData('categories.json') ?? [], JSON_UNESCAPED_UNICODE);
    elseif ($m === 'POST') {
        saveData('categories.json', $input['categories'] ?? []);
        echo json_encode(['success' => true]);
    }
} elseif ($p === 'requests') {
    if ($m === 'GET') echo json_encode(loadData('requests.json') ?? [], JSON_UNESCAPED_UNICODE);
    elseif ($m === 'POST' && isset($input['action']) && $input['action'] === 'add') {
        $c = loadData('requests.json') ?? [];
        array_unshift($c, $input['request']);
        saveData('requests.json', $c);
        echo json_encode(['success' => true]);
    }
} else {
    echo json_encode([
        'routes' => loadData('routes.json') ?? [],
        'services' => loadData('services.json') ?? [],
        'categories' => loadData('categories.json') ?? [],
        'requests' => loadData('requests.json') ?? []
    ], JSON_UNESCAPED_UNICODE);
}