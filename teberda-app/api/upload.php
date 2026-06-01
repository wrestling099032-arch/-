<?php
/**
 * API для загрузки изображений
 * Теберда & Домбай
 */

header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Handle preflight
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// Путь к папке с изображениями
define('UPLOAD_DIR', __DIR__ . '/../images');

// Создать папку если нет
if (!is_dir(UPLOAD_DIR)) {
    mkdir(UPLOAD_DIR, 0755, true);
}

// Генерировать уникальное имя файла
function generateFileName($originalName) {
    $ext = strtolower(pathinfo($originalName, PATHINFO_EXTENSION));
    $allowed = ['jpg', 'jpeg', 'png', 'gif', 'webp'];
    
    if (!in_array($ext, $allowed)) {
        $ext = 'jpg';
    }
    
    return uniqid('img_') . '_' . time() . '.' . $ext;
}

// Проверка базовой безопасности
function isValidImage($file) {
    // Проверяем MIME тип
    $allowedMimes = [
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp'
    ];
    
    // Для base64 данных просто проверяем расширение
    if (isset($file['name'])) {
        $ext = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
        $allowed = ['jpg', 'jpeg', 'png', 'gif', 'webp'];
        return in_array($ext, $allowed);
    }
    
    return true;
}

// Обработка загрузки файла
function handleFileUpload() {
    global $UPLOAD_ERR;
    
    if (!isset($_FILES['image'])) {
        echo json_encode(['success' => false, 'error' => 'No file uploaded']);
        return;
    }
    
    $file = $_FILES['image'];
    
    if ($file['error'] !== UPLOAD_ERR_OK) {
        echo json_encode(['success' => false, 'error' => 'Upload error: ' . $file['error']]);
        return;
    }
    
    if (!isValidImage($file)) {
        echo json_encode(['success' => false, 'error' => 'Invalid file type']);
        return;
    }
    
    // Ограничение размера (5MB)
    if ($file['size'] > 5 * 1024 * 1024) {
        echo json_encode(['success' => false, 'error' => 'File too large (max 5MB)']);
        return;
    }
    
    $filename = generateFileName($file['name']);
    $filepath = UPLOAD_DIR . '/' . $filename;
    
    if (move_uploaded_file($file['tmp_name'], $filepath)) {
        // Вернуть относительный путь
        $url = 'images/' . $filename;
        echo json_encode([
            'success' => true,
            'url' => $url,
            'path' => $filepath
        ]);
    } else {
        echo json_encode(['success' => false, 'error' => 'Failed to save file']);
    }
}

// Обработка base64 изображения
function handleBase64Upload() {
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!isset($input['data'])) {
        echo json_encode(['success' => false, 'error' => 'No data provided']);
        return;
    }
    
    // Проверяем что это base64 image
    if (preg_match('/^data:image\/(\w+);base64,/', $input['data'], $matches)) {
        $ext = strtolower($matches[1]);
        $allowed = ['jpeg', 'jpg', 'png', 'gif', 'webp'];
        
        if (!in_array($ext, $allowed)) {
            $ext = 'jpeg';
        }
        
        // Извлекаем данные
        $data = base64_decode(preg_replace('/^data:image\/\w+;base64,/', '', $input['data']));
        
        if ($data === false) {
            echo json_encode(['success' => false, 'error' => 'Invalid base64 data']);
            return;
        }
        
        // Проверяем размер (5MB decoded)
        if (strlen($data) > 5 * 1024 * 1024) {
            echo json_encode(['success' => false, 'error' => 'Image too large']);
            return;
        }
        
        $filename = uniqid('img_') . '_' . time() . '.' . $ext;
        $filepath = UPLOAD_DIR . '/' . $filename;
        
        if (file_put_contents($filepath, $data) !== false) {
            $url = 'images/' . $filename;
            echo json_encode([
                'success' => true,
                'url' => $url,
                'path' => $filepath
            ]);
        } else {
            echo json_encode(['success' => false, 'error' => 'Failed to save image']);
        }
    } else {
        echo json_encode(['success' => false, 'error' => 'Invalid data format']);
    }
}

// Точка входа
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!empty($_FILES)) {
        handleFileUpload();
    } else {
        handleBase64Upload();
    }
} else {
    echo json_encode(['error' => 'Method not allowed']);
}