from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


def main_menu(is_admin: bool = False):
    buttons = [
        [
            KeyboardButton(
                text="📅 Записаться на тестирование"
            )
        ],
        [
            KeyboardButton(text="ℹ️ О тестировании"),
            KeyboardButton(text="🛍️ Продукция TIENS")
        ],
        [
            KeyboardButton(
                text="📍 Адрес и контакты"
            ),
            KeyboardButton(
                # Точно такой же текст как в handlers!
                text="📊 Результаты наших программ"
            )
        ],
        [
            KeyboardButton(text="🏆 Сертификаты"),
            KeyboardButton(text="📱 Наши соц сети")
        ]
    ]

    if is_admin:
        buttons.append([
            KeyboardButton(text="🔐 Админ панель")
        ])

    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    return keyboard


def client_type_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🆕 Первый раз (первичка)"
                )
            ],
            [
                KeyboardButton(
                    text="🔄 Уже был(а) (повторник)"
                )
            ],
            [KeyboardButton(text="🚫 Отменить запись")]
        ],
        resize_keyboard=True
    )
    return keyboard


def yes_no_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="✅ Да"),
                KeyboardButton(text="❌ Нет")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚫 Отменить запись")]
        ],
        resize_keyboard=True
    )
    return keyboard


def dates_keyboard(dates: list):
    buttons = []
    for date in dates:
        parts = date.split("-")
        pretty_date = (
            f"{parts[2]}.{parts[1]}.{parts[0]}"
        )
        buttons.append([
            InlineKeyboardButton(
                text=f"📅 {pretty_date}",
                callback_data=f"date_{date}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            text="🚫 Отмена",
            callback_data="cancel_booking"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def times_keyboard(times: list, date: str):
    buttons = []
    row = []
    for time in times:
        row.append(
            InlineKeyboardButton(
                text=f"🕐 {time}",
                callback_data=f"time_{date}_{time}"
            )
        )
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([
        InlineKeyboardButton(
            text="◀️ Назад к датам",
            callback_data="back_to_dates"
        )
    ])
    buttons.append([
        InlineKeyboardButton(
            text="🚫 Отмена",
            callback_data="cancel_booking"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_keyboard():
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Подтвердить запись",
                callback_data="confirm_booking"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data="cancel_booking"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def categories_keyboard(categories: list):
    buttons = []
    for cat_id, name, emoji in categories:
        buttons.append([
            InlineKeyboardButton(
                text=f"{emoji} {name}",
                callback_data=f"category_{cat_id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="to_main_menu"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_keyboard(products: list, category_id: int):
    buttons = []
    for prod_id, name, description, price, *_ in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"🔹 {name} — {price}",
                callback_data=f"product_{prod_id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            text="◀️ Назад к категориям",
            callback_data="back_to_categories"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_menu_keyboard():
    buttons = [
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="to_main_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def certificates_keyboard(
    certs: list,
    current_index: int = 0
):
    """
    Кнопки для сертификатов
    С выбором номера и листанием
    """
    total = len(certs)
    buttons = []

    # Кнопки листания
    if total > 1:
        nav_row = []

        # Кнопка назад
        prev_index = (current_index - 1) % total
        nav_row.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"cert_page_{prev_index}"
            )
        )

        # Текущий номер
        nav_row.append(
            InlineKeyboardButton(
                text=f"{current_index + 1}/{total}",
                callback_data="cert_current"
            )
        )

        # Кнопка вперёд
        next_index = (current_index + 1) % total
        nav_row.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"cert_page_{next_index}"
            )
        )

        buttons.append(nav_row)

    # Кнопки выбора номера (по 5 в ряд)
    if total > 1:
        row = []
        for i in range(total):
            # Текущий сертификат помечаем
            text = (
                f"• {i + 1} •"
                if i == current_index
                else str(i + 1)
            )
            row.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"cert_page_{i}"
                )
            )
            # По 5 кнопок в ряд
            if len(row) == 5:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

    # Кнопка главного меню
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="to_main_menu"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)