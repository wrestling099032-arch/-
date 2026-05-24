from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)


def admin_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Управление расписанием")],
            [KeyboardButton(text="📝 Записи клиентов")],
            [KeyboardButton(text="📢 Рассылка"), KeyboardButton(text="🛍 Продукция")],
            [KeyboardButton(text="🏆 Сертификаты"), KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🚪 Выйти из админки")]
        ],
        resize_keyboard=True
    )
    return keyboard


def schedule_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить дату и время")],
            [KeyboardButton(text="👁 Посмотреть расписание")],
            [KeyboardButton(text="🔒 Заблокировать слот"),
             KeyboardButton(text="🔓 Разблокировать слот")],
            [KeyboardButton(text="🗑 Удалить дату")],
            [KeyboardButton(text="🔙 Назад в админку")]
        ],
        resize_keyboard=True
    )
    return keyboard


def lunch_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да добавить обед"),
             KeyboardButton(text="❌ Нет без обеда")],
            [KeyboardButton(text="🚫 Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard


def bookings_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Записи на сегодня")],
            [KeyboardButton(text="🗓 Записи на другую дату")],
            [KeyboardButton(text="➕ Добавить запись вручную")],
            [KeyboardButton(text="❌ Отменить запись клиента")],
            [KeyboardButton(text="🔙 Назад в админку")]
        ],
        resize_keyboard=True
    )
    return keyboard


def settings_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Изменить адрес")],
            [KeyboardButton(text="📞 Изменить контакты")],
            [KeyboardButton(text="📝 Изменить текст о тестировании")],
            [KeyboardButton(text="💳 Изменить реквизиты оплаты")],
            [KeyboardButton(text="💰 Изменить суммы предоплат")],
            [KeyboardButton(text="🌐 Социальные сети")],
            [KeyboardButton(text="⭐ Редактировать результаты")],
            [KeyboardButton(text="🔙 Назад в админку")]
        ],
        resize_keyboard=True
    )
    return keyboard


def prepayment_amounts_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔵 Сумма для первички")],
            [KeyboardButton(text="🟢 Сумма для повторника")],
            [KeyboardButton(text="🔙 Назад в настройки")]
        ],
        resize_keyboard=True
    )
    return keyboard


def socials_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✈️ Изменить Telegram")],
            [KeyboardButton(text="📱 Изменить WhatsApp")],
            [KeyboardButton(text="💬 Изменить BIP")],
            [KeyboardButton(text="🔙 Назад в настройки")]
        ],
        resize_keyboard=True
    )
    return keyboard


def faq_admin_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить результат")],
            [KeyboardButton(text="🗑 Удалить результат")],
            [KeyboardButton(text="👁 Посмотреть все результаты")],
            [KeyboardButton(text="🔙 Назад в настройки")]
        ],
        resize_keyboard=True
    )
    return keyboard


def certificates_admin_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить сертификат")],
            [KeyboardButton(text="🗑 Удалить сертификат")],
            [KeyboardButton(text="🔙 Назад в админку")]
        ],
        resize_keyboard=True
    )
    return keyboard


def products_admin_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить категорию")],
            [KeyboardButton(text="➕ Добавить продукт")],
            [KeyboardButton(text="✏️ Редактировать продукт")],
            [KeyboardButton(text="🗑 Удалить продукт"),
             KeyboardButton(text="🗑 Удалить категорию")],
            [KeyboardButton(text="🔙 Назад в админку")]
        ],
        resize_keyboard=True
    )
    return keyboard


def cancel_admin_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚫 Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard


def skip_photo_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏭ Пропустить фото")],
            [KeyboardButton(text="🚫 Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard


def approve_booking_keyboard(booking_id: int):
    """Кнопки одобрения/отклонения записи"""
    buttons = [
        [InlineKeyboardButton(
            text="✅ Одобрить запись",
            callback_data=f"approve_{booking_id}"
        )],
        [InlineKeyboardButton(
            text="❌ Отклонить запись",
            callback_data=f"reject_{booking_id}"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_dates_keyboard(dates: list, action: str = "view"):
    """
    Формирует инлайн-клавиатуру с датами.
    callback_data: {action}_{date}
    Например: view_date_2025-01-25
    """
    buttons = []
    for date in dates:
        parts = date.split("-")
        pretty_date = f"{parts[2]}.{parts[1]}.{parts[0]}"
        buttons.append([
            InlineKeyboardButton(
                text=f"📅 {pretty_date}",
                callback_data=f"{action}_{date}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            text="🚫 Отмена",
            callback_data="admin_cancel"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_slots_keyboard(slots: list, date: str, action: str):
    """
    ИСПРАВЛЕНО: используем | как разделитель в callback_data
    Формат: {action}|{date}|{time}
    Например: manualtime|2025-01-25|10:00
    blockslot|2025-01-25|10:00
    
    Это решает проблему с split("_") когда дата содержит дефисы
    """
    buttons = []
    row = []
    for time, status in slots:
        if status == "free":
            emoji = "🟢"
        elif status == "booked":
            emoji = "🔴"
        elif status == "lunch":
            emoji = "🍽"
        else:
            emoji = "⛔"

        row.append(
            InlineKeyboardButton(
                text=f"{emoji} {time}",
                # КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: разделитель | вместо пробела
                callback_data=f"{action}|{date}|{time}"
            )
        )
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([
        InlineKeyboardButton(
            text="🚫 Отмена",
            callback_data="admin_cancel"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_categories_keyboard(categories: list, action: str):
    buttons = []
    for cat_id, name, emoji in categories:
        buttons.append([
            InlineKeyboardButton(
                text=f"{emoji} {name}",
                callback_data=f"{action}_{cat_id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            text="🚫 Отмена",
            callback_data="admin_cancel"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_products_keyboard(products: list, action: str):
    buttons = []
    for prod_id, name, description, price, *_ in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"🛍 {name}",
                callback_data=f"{action}_{prod_id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            text="🚫 Отмена",
            callback_data="admin_cancel"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_certs_keyboard(certs: list):
    """Список сертификатов для удаления"""
    buttons = []
    for cert_id, title, photo_id in certs:
        buttons.append([
            InlineKeyboardButton(
                text=f"🏆 {title}",
                callback_data=f"delcert_{cert_id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            text="🚫 Отмена",
            callback_data="admin_cancel"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def manual_booking_type_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔵 Первичка (40 мин)")],
            [KeyboardButton(text="🟢 Повторник (20 мин)")],
            [KeyboardButton(text="🚫 Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard


def manual_yes_no_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="✅ Да"),
                KeyboardButton(text="❌ Нет")
            ],
            [KeyboardButton(text="🚫 Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard