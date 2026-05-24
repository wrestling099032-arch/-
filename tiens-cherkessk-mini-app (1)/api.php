<?php
// ============================================================
// api.php — TIENS Backend API
// Разместить в корне сайта рядом с index.html и admin.html
// ============================================================

// ⚠️ ЗАМЕНИТЕ ПЕРЕД ДЕПЛОЕМ:
define('ADMIN_KEY', 'tiens_server_key_2026');
define('DATA_FILE', __DIR__ . '/data.json');
define('IMAGES_DIR', __DIR__ . '/images/');
define('SITE_URL', 'https://' . $_SERVER['HTTP_HOST']);

// ============================================================
// CORS и заголовки
// ============================================================
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, X-Requested-With');
header('X-Content-Type-Options: nosniff');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

// ============================================================
// Пустая структура по умолчанию
// ============================================================
function emptyStructure(): array {
    return [
        'products'   => [],
        'categories' => [],
        'reviews'    => [],
        'content'    => (object)[],
        'contacts'   => (object)[],
    ];
}

// ============================================================
// Читаем data.json
// ============================================================
function readData(): array {
    if (!file_exists(DATA_FILE)) {
        return emptyStructure();
    }
    $raw = file_get_contents(DATA_FILE);
    if ($raw === false) {
        error_log('[TIENS API] Cannot read ' . DATA_FILE);
        return emptyStructure();
    }
    $data = json_decode($raw, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        error_log('[TIENS API] JSON decode error: ' . json_last_error_msg());
        return emptyStructure();
    }
    // Гарантируем все ключи
    $empty = emptyStructure();
    foreach ($empty as $k => $v) {
        if (!isset($data[$k])) $data[$k] = $v;
    }
    return $data;
}

// ============================================================
// Записываем data.json
// ============================================================
function writeData(array $data): bool {
    $json = json_encode(
        $data,
        JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES
    );
    if ($json === false) {
        error_log('[TIENS API] JSON encode error: ' . json_last_error_msg());
        return false;
    }
    // Атомарная запись через временный файл
    $tmp = DATA_FILE . '.tmp';
    if (file_put_contents($tmp, $json, LOCK_EX) === false) {
        error_log('[TIENS API] Cannot write tmp file');
        return false;
    }
    return rename($tmp, DATA_FILE);
}

// ============================================================
// Проверка adminKey
// ============================================================
function checkAdminKey(): bool {
    $key = $_GET['adminKey'] ?? '';
    return hash_equals(ADMIN_KEY, $key);
}

// ============================================================
// Валидация структуры входящих данных
// ============================================================
function validatePayload(array $data): array {
    $errors = [];

    if (isset($data['products']) && !is_array($data['products'])) {
        $errors[] = 'products must be array';
    }
    if (isset($data['categories']) && !is_array($data['categories'])) {
        $errors[] = 'categories must be array';
    }
    if (isset($data['reviews']) && !is_array($data['reviews'])) {
        $errors[] = 'reviews must be array';
    }

    // Валидация товаров
    if (isset($data['products']) && is_array($data['products'])) {
        foreach ($data['products'] as $i => $p) {
            if (empty($p['name'])) {
                $errors[] = "Product[$i]: name is required";
            }
            if (!isset($p['price']) || !is_numeric($p['price'])) {
                $errors[] = "Product[$i]: price must be numeric";
            }
        }
    }

    return $errors;
}

// ============================================================
// Обработка загрузки изображения
// ============================================================
function handleUpload(): void {
    if (!checkAdminKey()) {
        http_response_code(403);
        echo json_encode(['success' => false, 'error' => 'Forbidden']);
        exit;
    }

    // Создаём папку images если нет
    if (!is_dir(IMAGES_DIR)) {
        if (!mkdir(IMAGES_DIR, 0755, true)) {
            http_response_code(500);
            echo json_encode(['success' => false, 'error' => 'Cannot create images dir']);
            exit;
        }
        // Создаём images/.htaccess при первом создании папки
        createImagesHtaccess();
    }

    // === Загрузка по URL ===
    if (!empty($_POST['image_url'])) {
        $url = trim($_POST['image_url']);

        if (!filter_var($url, FILTER_VALIDATE_URL)) {
            http_response_code(400);
            echo json_encode(['success' => false, 'error' => 'Invalid URL']);
            exit;
        }

        $ext = strtolower(pathinfo(parse_url($url, PHP_URL_PATH), PATHINFO_EXTENSION));
        $allowed = ['jpg', 'jpeg', 'png', 'webp', 'gif'];
        if (!in_array($ext, $allowed, true)) {
            http_response_code(400);
            echo json_encode(['success' => false, 'error' => 'Invalid image extension']);
            exit;
        }

        // Возвращаем URL как есть (не скачиваем — безопасно для shared хостинга)
        echo json_encode(['success' => true, 'url' => $url]);
        exit;
    }

    // === Загрузка файла ===
    if (empty($_FILES['image'])) {
        http_response_code(400);
        echo json_encode(['success' => false, 'error' => 'No image provided']);
        exit;
    }

    $file = $_FILES['image'];

    // Проверка ошибок загрузки
    if ($file['error'] !== UPLOAD_ERR_OK) {
        $errMessages = [
            UPLOAD_ERR_INI_SIZE   => 'File too large (php.ini limit)',
            UPLOAD_ERR_FORM_SIZE  => 'File too large (form limit)',
            UPLOAD_ERR_PARTIAL    => 'File partially uploaded',
            UPLOAD_ERR_NO_FILE    => 'No file uploaded',
            UPLOAD_ERR_NO_TMP_DIR => 'Missing temp folder',
            UPLOAD_ERR_CANT_WRITE => 'Cannot write file',
            UPLOAD_ERR_EXTENSION  => 'Upload stopped by extension',
        ];
        $msg = $errMessages[$file['error']] ?? 'Upload error ' . $file['error'];
        http_response_code(400);
        echo json_encode(['success' => false, 'error' => $msg]);
        exit;
    }

    // Размер: max 5MB
    if ($file['size'] > 5 * 1024 * 1024) {
        http_response_code(400);
        echo json_encode(['success' => false, 'error' => 'File too large. Max 5MB']);
        exit;
    }

    // Проверка MIME через finfo (не полагаемся на $_FILES['type'])
    $finfo = new finfo(FILEINFO_MIME_TYPE);
    $mime  = $finfo->file($file['tmp_name']);
    $allowedMimes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];

    if (!in_array($mime, $allowedMimes, true)) {
        http_response_code(400);
        echo json_encode(['success' => false, 'error' => 'Invalid file type: ' . $mime]);
        exit;
    }

    // Генерируем безопасное имя файла
    $baseName = 'product_' . time() . '_' . bin2hex(random_bytes(4));

    // Попытка конвертации в WebP через GD
    $savedName = trySaveAsWebP($file['tmp_name'], $mime, $baseName);

    if ($savedName === null) {
        // Fallback: сохраняем в оригинальном формате
        $extMap = [
            'image/jpeg' => 'jpg',
            'image/png'  => 'png',
            'image/webp' => 'webp',
            'image/gif'  => 'gif',
        ];
        $ext = $extMap[$mime] ?? 'jpg';
        $savedName = $baseName . '.' . $ext;
        $destPath  = IMAGES_DIR . $savedName;

        // Защита от path traversal
        $realDest = realpath(IMAGES_DIR) . DIRECTORY_SEPARATOR . basename($savedName);
        if (!move_uploaded_file($file['tmp_name'], $realDest)) {
            error_log('[TIENS API] Cannot move uploaded file to ' . $realDest);
            http_response_code(500);
            echo json_encode(['success' => false, 'error' => 'Cannot save file']);
            exit;
        }
    }

    $url = SITE_URL . '/images/' . $savedName;
    echo json_encode(['success' => true, 'url' => $url]);
    exit;
}

// ============================================================
// Конвертация в WebP через GD
// ============================================================
function trySaveAsWebP(string $tmpPath, string $mime, string $baseName): ?string {
    if (!function_exists('imagewebp')) {
        return null; // GD не поддерживает WebP
    }

    try {
        switch ($mime) {
            case 'image/jpeg':
                $img = @imagecreatefromjpeg($tmpPath);
                break;
            case 'image/png':
                $img = @imagecreatefrompng($tmpPath);
                break;
            case 'image/webp':
                $img = @imagecreatefromwebp($tmpPath);
                break;
            default:
                return null;
        }

        if (!$img) return null;

        // Для PNG сохраняем прозрачность
        if ($mime === 'image/png') {
            imagepalettetotruecolor($img);
            imagealphablending($img, true);
            imagesavealpha($img, true);
        }

        $fileName = $baseName . '.webp';
        $destPath = IMAGES_DIR . $fileName;

        $result = imagewebp($img, $destPath, 85); // качество 85%
        imagedestroy($img);

        if (!$result) {
            error_log('[TIENS API] imagewebp failed for ' . $destPath);
            return null;
        }

        // Защита: проверяем что файл реально в папке images
        $real = realpath($destPath);
        $dir  = realpath(IMAGES_DIR);
        if ($real === false || strpos($real, $dir) !== 0) {
            @unlink($destPath);
            return null;
        }

        return $fileName;

    } catch (Throwable $e) {
        error_log('[TIENS API] GD error: ' . $e->getMessage());
        return null;
    }
}

// ============================================================
// Создаём images/.htaccess при создании папки
// ============================================================
function createImagesHtaccess(): void {
    $htaccess = IMAGES_DIR . '.htaccess';
    if (!file_exists($htaccess)) {
        $content = <<<HTACCESS
# Запрет выполнения PHP в папке images
<FilesMatch "\.(php|php3|php4|php5|php7|phtml|pl|py|cgi|sh)$">
    Order allow,deny
    Deny from all
</FilesMatch>

Options -ExecCGI
AddHandler cgi-script .php .pl .py .cgi

# Разрешаем только изображения
<FilesMatch "\.(jpg|jpeg|png|gif|webp|svg|ico)$">
    Order allow,deny
    Allow from all
</FilesMatch>
HTACCESS;
        file_put_contents($htaccess, $content);
    }
}

// ============================================================
// РОУТЕР
// ============================================================
$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? '';

// POST /api.php?action=upload&adminKey=...
if ($method === 'POST' && $action === 'upload') {
    handleUpload();
    exit;
}

// GET /api.php — вернуть данные
if ($method === 'GET') {
    $data = readData();
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

// POST /api.php?adminKey=... — сохранить данные
if ($method === 'POST') {
    if (!checkAdminKey()) {
        http_response_code(403);
        echo json_encode(['success' => false, 'error' => 'Forbidden: invalid admin key']);
        exit;
    }

    // Читаем тело запроса
    $body = file_get_contents('php://input');
    if (empty($body)) {
        http_response_code(400);
        echo json_encode(['success' => false, 'error' => 'Empty request body']);
        exit;
    }

    $payload = json_decode($body, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        http_response_code(400);
        echo json_encode(['success' => false, 'error' => 'Invalid JSON: ' . json_last_error_msg()]);
        exit;
    }

    // Валидация
    $errors = validatePayload($payload);
    if (!empty($errors)) {
        http_response_code(422);
        echo json_encode(['success' => false, 'errors' => $errors]);
        exit;
    }

    // Читаем существующие данные и мержим
    $existing = readData();
    $allowed  = ['products', 'categories', 'reviews', 'content', 'contacts'];

    foreach ($allowed as $key) {
        if (array_key_exists($key, $payload)) {
            $existing[$key] = $payload[$key];
        }
    }

    if (!writeData($existing)) {
        http_response_code(500);
        echo json_encode(['success' => false, 'error' => 'Cannot write data.json']);
        exit;
    }

    echo json_encode([
        'success'  => true,
        'message'  => 'Data saved successfully',
        'products' => count($existing['products'] ?? []),
        'reviews'  => count($existing['reviews'] ?? []),
        'saved_at' => date('Y-m-d H:i:s'),
    ]);
    exit;
}

// Неизвестный метод
http_response_code(405);
echo json_encode(['success' => false, 'error' => 'Method not allowed']);