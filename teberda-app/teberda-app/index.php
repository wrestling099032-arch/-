<?php
/**
 * Точка входа - перенаправляет на index.html
 * Теберда & Домбай
 */

// Если запрашивают данные API - пропускаем
$uri = $_SERVER['REQUEST_URI'];
if (strpos($uri, '/api/') === 0) {
    return false;
}

// Перенаправляем на index.html
$file = __DIR__ . '/index.html';
if (file_exists($file)) {
    readfile($file);
} else {
    echo "index.html not found";
}