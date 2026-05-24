from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

import database as db
from keyboards import client_kb, admin_kb
from config import ADMIN_ID

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ==================== СТАРТ ====================

@router.message(CommandStart())
async def start(message: Message):
    await db.add_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or ""
    )

    admin = is_admin(message.from_user.id)

    await message.answer(
        f"👋 Здравствуйте, "
        f"{message.from_user.first_name}!\n\n"
        "Добро пожаловать в TIENS Черкесск! 🌿\n\n"
        "Здесь вы можете:\n"
        "📅 Записаться на тестирование\n"
        "🛍️ Ознакомиться с продукцией TIENS\n"
        "🏆 Посмотреть наши сертификаты\n\n"
        "Выберите что вас интересует 👇",
        reply_markup=client_kb.main_menu(
            is_admin=admin
        )
    )


# ==================== КНОПКА АДМИН ПАНЕЛИ ====================

@router.message(F.text == "🔐 Админ панель")
async def admin_panel_button(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа")
        return
    await message.answer(
        "🔐 Добро пожаловать в админ панель!",
        reply_markup=admin_kb.admin_main_menu()
    )


# ==================== О ТЕСТИРОВАНИИ ====================

@router.message(F.text == "ℹ️ О тестировании")
async def about_testing(message: Message):
    text = await db.get_setting("about_testing")
    await message.answer(
        text,
        reply_markup=client_kb.back_to_menu_keyboard()
    )


# ==================== АДРЕС И КОНТАКТЫ ====================

@router.message(F.text == "📍 Адрес и контакты")
async def address_contacts(message: Message):
    address = await db.get_setting("address")
    contacts = await db.get_setting("contacts")
    await message.answer(
        f"📍 Адрес:\n{address}\n\n"
        f"📞 Контакты:\n{contacts}",
        reply_markup=client_kb.back_to_menu_keyboard()
    )


# ==================== РЕЗУЛЬТАТЫ ПРОГРАММ ====================

# ==================== РЕЗУЛЬТАТЫ ПРОГРАММ ====================

@router.message(
    F.text == "📊 Результаты наших программ"
)
async def show_results(message: Message):
    try:
        faqs = await db.get_faq()

        if not faqs:
            await message.answer(
                "📊 Результаты пока не добавлены\n\n"
                "Загляните позже!",
                reply_markup=(
                    client_kb.back_to_menu_keyboard()
                )
            )
            return

        # Разбиваем на части если текст длинный
        messages = []
        current_text = (
            "📊 Результаты наших программ:\n\n"
        )

        for i, (faq_id, question, answer) in enumerate(
            faqs, 1
        ):
            # Один блок результата
            block = (
                f"🔹 {i}. {question}\n"
                f"💬 {answer}\n\n"
            )

            # Если текущее сообщение + блок
            # больше 4000 символов — начинаем новое
            if len(current_text) + len(block) > 4000:
                messages.append(current_text)
                current_text = block
            else:
                current_text += block

        # Добавляем последнюю часть
        if current_text:
            messages.append(current_text)

        # Отправляем все части
        for i, text in enumerate(messages):
            # Кнопку добавляем только к последнему
            if i == len(messages) - 1:
                await message.answer(
                    text,
                    reply_markup=(
                        client_kb.back_to_menu_keyboard()
                    )
                )
            else:
                await message.answer(text)

    except Exception as e:
        print(f"Ошибка результаты: {e}")
        await message.answer(
            "❌ Произошла ошибка\n"
            "Попробуйте позже",
            reply_markup=(
                client_kb.back_to_menu_keyboard()
            )
        )

# ==================== СОЦИАЛЬНЫЕ СЕТИ ====================

@router.message(F.text == "📱 Наши соц сети")
async def show_socials(message: Message):
    socials = await db.get_social_links()
    if not socials:
        await message.answer(
            "📱 Социальные сети пока не добавлены",
            reply_markup=(
                client_kb.back_to_menu_keyboard()
            )
        )
        return
    emojis = {
        "Telegram": "✈️",
        "WhatsApp": "💬",
        "BIP": "🔵"
    }
    text = "📱 Наши социальные сети:\n\n"
    for social_id, name, url in socials:
        emoji = emojis.get(name, "🔗")
        text += f"{emoji} {name}:\n{url}\n\n"
    await message.answer(
        text,
        reply_markup=client_kb.back_to_menu_keyboard()
    )


# ==================== ПРОДУКЦИЯ ====================

@router.message(F.text == "🛍️ Продукция TIENS")
async def show_products(message: Message):
    categories = await db.get_categories()
    if not categories:
        await message.answer(
            "🛍️ Продукция пока не добавлена\n"
            "Загляните позже!",
            reply_markup=(
                client_kb.back_to_menu_keyboard()
            )
        )
        return
    await message.answer(
        "🛍️ Продукция TIENS\n\n"
        "Выберите категорию:",
        reply_markup=client_kb.categories_keyboard(
            categories
        )
    )


@router.callback_query(
    F.data.startswith("category_")
)
async def show_category_products(
    callback: CallbackQuery
):
    category_id = int(callback.data.split("_")[1])
    products = await db.get_products_by_category(
        category_id
    )
    categories = await db.get_categories()

    category_name = ""
    category_emoji = ""
    for cat_id, name, emoji in categories:
        if cat_id == category_id:
            category_name = name
            category_emoji = emoji
            break

    if not products:
        await callback.message.edit_text(
            f"{category_emoji} {category_name}\n\n"
            "В этой категории пока нет продуктов",
            reply_markup=client_kb.categories_keyboard(
                categories
            )
        )
        return

    await callback.message.edit_text(
        f"{category_emoji} {category_name}\n\n"
        "Выберите продукт:",
        reply_markup=client_kb.products_keyboard(
            products, category_id
        )
    )


@router.callback_query(
    F.data.startswith("product_")
)
async def show_product_detail(
    callback: CallbackQuery
):
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product_by_id(product_id)

    if not product:
        await callback.answer("Продукт не найден")
        return

    (prod_id, name, description,
     price, photo_id, category_id) = product

    products = await db.get_products_by_category(
        category_id
    )

    text = (
        f"🔹 {name}\n\n"
        f"📝 Описание:\n{description}\n\n"
        f"💰 Цена: {price}"
    )
    keyboard = client_kb.products_keyboard(
        products, category_id
    )

    if photo_id:
        try:
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=photo_id,
                caption=text,
                reply_markup=keyboard
            )
        except Exception:
            await callback.message.answer(
                text,
                reply_markup=keyboard
            )
    else:
        try:
            await callback.message.edit_text(
                text,
                reply_markup=keyboard
            )
        except Exception:
            await callback.message.answer(
                text,
                reply_markup=keyboard
            )


@router.callback_query(
    F.data == "back_to_categories"
)
async def back_to_categories(
    callback: CallbackQuery
):
    categories = await db.get_categories()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "🛍️ Продукция TIENS\n\n"
        "Выберите категорию:",
        reply_markup=client_kb.categories_keyboard(
            categories
        )
    )


@router.callback_query(F.data == "to_main_menu")
async def to_main_menu(callback: CallbackQuery):
    admin = is_admin(callback.from_user.id)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=client_kb.main_menu(
            is_admin=admin
        )
    )