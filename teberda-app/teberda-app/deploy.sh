#!/bin/bash
#
# Автоматический деплой на Sweb
# Теберда & Домбай
#

set -e

echo "========================================"
echo "Теберда & Домбай - Деплой"
echo "========================================"
echo ""

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Проверка SSH доступа
check_ssh() {
    echo -e "${YELLOW}Проверка SSH доступа...${NC}"
    if ! command -v ssh &> /dev/null; then
        echo -e "${RED}SSH не установлен${NC}"
        exit 1
    fi
    echo -e "${GREEN}SSH доступен${NC}"
}

# Клонирование репозитория
clone_repo() {
    echo ""
    echo -e "${YELLOW}Клонирование репозитория...${NC}"
    
    REPO_URL="https://github.com/wrestling099032-arch/-.git"
    TARGET_DIR="$1"
    
    if [ -d "$TARGET_DIR" ]; then
        echo -e "${YELLOW}Папка уже существует, обновляю...${NC}"
        cd "$TARGET_DIR"
        git pull
    else
        git clone "$REPO_URL" "$TARGET_DIR"
    fi
    
    echo -e "${GREEN}Репозиторий склонирован${NC}"
}

# Добавление PHP файлов
add_php() {
    echo ""
    echo -e "${YELLOW}Добавление PHP файлов...${NC}"
    
    APP_DIR="$1"
    
    # Создаём структуру папок
    mkdir -p "$APP_DIR/api"
    mkdir -p "$APP_DIR/data"
    mkdir -p "$APP_DIR/images"
    
    # Копируем PHP файлы
    cat > "$APP_DIR/api/data.php" << 'PHPEOF'
<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
$input = json_decode(file_get_contents('php://input'), true) ?? [];
define('DATA_DIR', __DIR__ . '/../data');
if (!is_dir(DATA_DIR)) mkdir(DATA_DIR, 0755, true);
function saveData($f, $d) { file_put_contents(DATA_DIR.'/'.$f, json_encode($d, JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT)); }
function loadData($f) { $p=DATA_DIR.'/'.$f; return file_exists($p)?json_decode(file_get_contents($p), true):null; }
$p = $_GET['path'] ?? '';
$m = $_SERVER['REQUEST_METHOD'];
if ($p === 'routes') {
    if ($m === 'GET') { echo json_encode(loadData('routes.json') ?? [], JSON_UNESCAPED_UNICODE); }
    elseif ($m === 'POST' && isset($input['action'])) {
        $c = loadData('routes.json') ?? [];
        if ($input['action'] === 'save') {
            if (isset($input['routeSettings'])) $c['routeSettings'] = $input['routeSettings'];
            if (isset($input['customRoutes'])) $c['customRoutes'] = $input['customRoutes'];
            saveData('routes.json', $c);
            echo json_encode(['success' => true]);
        }
    }
} elseif ($p === 'services') {
    if ($m === 'GET') { echo json_encode(loadData('services.json') ?? [], JSON_UNESCAPED_UNICODE); }
    elseif ($m === 'POST' && isset($input['action']) && $input['action'] === 'save') {
        saveData('services.json', $input['services'] ?? []);
        echo json_encode(['success' => true]);
    }
} elseif ($p === 'categories') {
    if ($m === 'GET') { echo json_encode(loadData('categories.json') ?? [], JSON_UNESCAPED_UNICODE); }
    elseif ($m === 'POST') {
        saveData('categories.json', $input['categories'] ?? []);
        echo json_encode(['success' => true]);
    }
} elseif ($p === 'requests') {
    if ($m === 'GET') { echo json_encode(loadData('requests.json') ?? [], JSON_UNESCAPED_UNICODE); }
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
PHPEOF
    
    cat > "$APP_DIR/api/upload.php" << 'PHPEOF'
<?php
header('Access-Control-Allow-Origin: *');
define('UPLOAD_DIR', __DIR__ . '/../images');
if (!is_dir(UPLOAD_DIR)) mkdir(UPLOAD_DIR, 0755, true);
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!empty($_FILES) && isset($_FILES['image'])) {
        $f = $_FILES['image'];
        if ($f['error'] === UPLOAD_ERR_OK && $f['size'] <= 5*1024*1024) {
            $ext = strtolower(pathinfo($f['name'], PATHINFO_EXTENSION));
            $filename = uniqid('img_').'_'.time().'.'.$ext;
            if (move_uploaded_file($f['tmp_name'], UPLOAD_DIR.'/'.$filename)) {
                echo json_encode(['success' => true, 'url' => 'images/'.$filename]);
                exit;
            }
        }
    }
    $input = json_decode(file_get_contents('php://input'), true);
    if (isset($input['data']) && preg_match('/^data:image\/(\w+);base64,/', $input['data'], $m)) {
        $data = base64_decode(preg_replace('/^data:image\/\w+;base64,/', '', $input['data']));
        $ext = strtolower($m[1]);
        $filename = uniqid('img_').'_'.time().'.'.$ext;
        if (file_put_contents(UPLOAD_DIR.'/'.$filename, $data)) {
            echo json_encode(['success' => true, 'url' => 'images/'.$filename]);
            exit;
        }
    }
    echo json_encode(['success' => false, 'error' => 'Upload failed']);
}
PHPEOF
    
    cat > "$APP_DIR/api/init.php" << 'PHPEOF'
<?php
$dataDir = __DIR__ . '/../data';
if (!is_dir($dataDir)) mkdir($dataDir, 0755, true);
$cats = [['id'=>'housing','icon'=>'fa-bed','name'=>'Жильё','cities'=>['Теберда','Домбай','Архыз'],'subcategories'=>[['id'=>'hotels','name'=>'Гостиницы'],['id'=>'apart','name'=>'Квартиры']]],['id'=>'food','icon'=>'fa-utensils','name'=>'Еда','cities'=>['Теберда','Домбай','Архыз']],['id'=>'transport','icon'=>'fa-bus','name'=>'Транспорт','cities'=>['Теберда','Домбай','Архыз']],['id'=>'rental','icon'=>'fa-skiing','name'=>'Аренда','cities'=>['Теберда','Домбай','Архыз']],['id'=>'excursions','icon'=>'fa-compass','name'=>'Экскурсии','cities'=>['Теберда','Домбай','Архыз']],['id'=>'medical','icon'=>'fa-first-aid','name'=>'Медицина','cities'=>['Теберда','Домбай','Архыз']],['id'=>'guide','icon'=>'fa-hiking','name'=>'Гиды','cities'=>['Теберда','Домбай','Архыз']],['id'=>'other','icon'=>'fa-ellipsis-h','name'=>'Прочее','cities'=>['Теберда','Домбай','Архыз']]];
if (!file_exists($dataDir.'/categories.json')) file_put_contents($dataDir.'/categories.json', json_encode($cats, JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT));
if (!file_exists($dataDir.'/routes.json')) file_put_contents($dataDir.'/routes.json', json_encode(['routeSettings'=>[],'customRoutes'=>[]], JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT));
if (!file_exists($dataDir.'/services.json')) file_put_contents($dataDir.'/services.json', '[]');
if (!file_exists($dataDir.'/requests.json')) file_put_contents($dataDir.'/requests.json', '[]');
echo "Данные инициализированы!";
PHPEOF
    
    echo -e "${GREEN}PHP файлы созданы${NC}"
}

# Создание index.php
add_index_php() {
    echo ""
    echo -e "${YELLOW}Создание index.php...${NC}"
    
    APP_DIR="$1"
    
    cat > "$APP_DIR/index.php" << 'PHPEOF'
<?php
$uri = $_SERVER['REQUEST_URI'];
if (strpos($uri, '/api/') === 0) return false;
$file = __DIR__ . '/index.html';
if (file_exists($file)) readfile($file);
else echo "index.html not found";
PHPEOF
    
    echo -e "${GREEN}index.php создан${NC}"
}

# Создание .htaccess
add_htaccess() {
    echo ""
    echo -e "${YELLOW}Создание .htaccess...${NC}"
    
    APP_DIR="$1"
    
    cat > "$APP_DIR/.htaccess" << 'HTACCESS'
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} -f
RewriteRule ^ - [L]
RewriteCond %{REQUEST_FILENAME} -d
RewriteRule ^ - [L]
RewriteCond %{REQUEST_URI} ^/api/
RewriteRule ^api/(.*)$ api/$1 [L]
RewriteRule ^ index.html [L]
<Files "data/*">
    Order Deny,Allow
    Deny from all
</Files>
Options -Indexes
HTACCESS
    
    cat > "$APP_DIR/api/.htaccess" << 'HTACCESS'
<Files "*.json">
    Order Deny,Allow
    Deny from all
</Files>
HTACCESS
    
    cat > "$APP_DIR/data/.htaccess" << 'HTACCESS'
Order Deny,Allow
Deny from all
HTACCESS
    
    echo -e "${GREEN}.htaccess файлы созданы${NC}"
}

# Инициализация данных
init_data() {
    echo ""
    echo -e "${YELLOW}Инициализация данных...${NC}"
    
    APP_DIR="$1"
    
    cd "$APP_DIR"
    php api/init.php 2>/dev/null || echo "PHP недоступен локально, запустите на сервере: php api/init.php"
    
    echo -e "${GREEN}Готово!${NC}"
}

# Главное меню
show_menu() {
    echo ""
    echo "Выберите действие:"
    echo "1 - Полный деплой (клонировать + настроить)"
    echo "2 - Только добавить PHP файлы в существующую папку"
    echo "3 - Создать архив для загрузки"
    echo ""
    read -p "Введите номер: " choice
    
    case $choice in
        1)
            read -p "Введите путь к папке проекта (например, ~/www/teberda-app): " target
            clone_repo "$target"
            add_php "$target"
            add_index_php "$target"
            add_htaccess "$target"
            init_data "$target"
            ;;
        2)
            read -p "Введите путь к папке проекта: " target
            add_php "$target"
            add_index_php "$target"
            add_htaccess "$target"
            init_data "$target"
            ;;
        3)
            echo "Используйте архив из этой папки проекта"
            ;;
        *)
            echo "Неверный выбор"
            ;;
    esac
}

# Запуск
check_ssh
show_menu

echo ""
echo -e "${GREEN}========================================"
echo "Деплой завершён!"
echo "========================================${NC}"
echo ""
echo "Следующие шаги:"
echo "1. Настройте домен в панели Sweb"
echo "2. Откройте http://ваш-домен/api/init.php"
echo "3. Откройте админку: http://ваш-домен/admin.html"