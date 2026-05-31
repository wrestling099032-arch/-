<?php
/**
 * Инициализация данных
 * Теберда & Домбай
 * 
 * Этот скрипт создаёт начальные данные если их нет
 * Запустить один раз после деплоя
 */

// Защита от прямого запуска
if (php_sapi_name() !== 'cli' && !isset($_GET['init'])) {
    die('Access denied');
}

header('Content-Type: text/plain; charset=utf-8');

$dataDir = __DIR__ . '/../data';
if (!is_dir($dataDir)) {
    mkdir($dataDir, 0755, true);
}

// Начальные данные для маршрутов
$defaultRoutes = [
    'routeSettings' => [],
    'customRoutes' => []
];

// Начальные данные для услуг
$defaultServices = [];

// Начальные данные для категорий
$defaultCategories = [
    ['id' => 'housing', 'icon' => 'fa-bed', 'name' => 'Жильё', 'cities' => ['Теберда', 'Домбай', 'Архыз']],
    ['id' => 'food', 'icon' => 'fa-utensils', 'name' => 'Еда', 'cities' => ['Теберда', 'Домбай', 'Архыз']],
    ['id' => 'transport', 'icon' => 'fa-bus', 'name' => 'Транспорт', 'cities' => ['Теберда', 'Домбай', 'Архыз']],
    ['id' => 'rental', 'icon' => 'fa-skiing', 'name' => 'Аренда', 'cities' => ['Теберда', 'Домбай', 'Архыз']],
    ['id' => 'excursions', 'icon' => 'fa-compass', 'name' => 'Экскурсии', 'cities' => ['Теберда', 'Домбай', 'Архыз']],
    ['id' => 'medical', 'icon' => 'fa-first-aid', 'name' => 'Медицина', 'cities' => ['Теберда', 'Домбай', 'Архыз']],
    ['id' => 'guide', 'icon' => 'fa-hiking', 'name' => 'Гиды', 'cities' => ['Теберда', 'Домбай', 'Архыз']],
    ['id' => 'other', 'icon' => 'fa-ellipsis-h', 'name' => 'Прочее', 'cities' => ['Теберда', 'Домбай', 'Архыз']]
];

// Начальные данные для заявок
$defaultRequests = [];

// Функция сохранения
function saveJson($filename, $data) {
    $filepath = __DIR__ . '/../data/' . $filename;
    $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    return file_put_contents($filepath, $json) !== false;
}

echo "=== Инициализация данных ===\n\n";

// Создаём файлы если их нет
if (!file_exists(__DIR__ . '/../data/routes.json')) {
    if (saveJson('routes.json', $defaultRoutes)) {
        echo "✓ routes.json создан\n";
    } else {
        echo "✗ Ошибка создания routes.json\n";
    }
} else {
    echo "- routes.json уже существует\n";
}

if (!file_exists(__DIR__ . '/../data/services.json')) {
    if (saveJson('services.json', $defaultServices)) {
        echo "✓ services.json создан\n";
    } else {
        echo "✗ Ошибка создания services.json\n";
    }
} else {
    echo "- services.json уже существует\n";
}

if (!file_exists(__DIR__ . '/../data/categories.json')) {
    if (saveJson('categories.json', $defaultCategories)) {
        echo "✓ categories.json создан\n";
    } else {
        echo "✗ Ошибка создания categories.json\n";
    }
} else {
    echo "- categories.json уже существует\n";
}

if (!file_exists(__DIR__ . '/../data/requests.json')) {
    if (saveJson('requests.json', $defaultRequests)) {
        echo "✓ requests.json создан\n";
    } else {
        echo "✗ Ошибка создания requests.json\n";
    }
} else {
    echo "- requests.json уже существует\n";
}

echo "\n=== Готово! ===\n";
echo "Теперь можете использовать админку.\n";