from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards import admin_kb
from config import ADMIN_ID

router = Router()


def is_admin(message: Message) -> bool:
    return message.from_user.id == ADMIN_ID


# ==================== СОСТОЯНИЯ ====================
class ProductStates(StatesGroup):
    # Добавление категории
    adding_category_name = State()
    adding_category_emoji = State()
    
    # Добавление продукта
    adding_product_category = State()
    adding_product_name = State()
    adding_product_description = State()
    adding_product_price = State()
    adding_product_photo = State()
    
    # Редактирование продукта
    editing_product_category = State()
    editing_product_choose = State()
    editing_product_name = State()
    editing_product_description = State()
    editing_product_price = State()
    editing_product_photo = State()
    
    # Удаление продукта
    deleting_product_category = State()
    deleting_product_choose = State()
    
    # Удаление категории
    deleting_category_choose = State()


# ==================== МЕНЮ ПРОДУКЦИИ ====================
@router.message(F.text == "🛍 Продукция")  # ← ИСПРАВЛЕНО: убран лишний пробел
async def products_admin(message: Message):
    if not is_admin(message):
        return
    
    await message.answer(
        "🛍 Управление продукцией:",
        reply_markup=admin_kb.products_admin_menu()
    )


# ==================== ДОБАВИТЬ КАТЕГОРИЮ ====================
@router.message(F.text == "➕ Добавить категорию")
async def add_category_start(
    message: Message, state: FSMContext
):
    if not is_admin(message):
        return
    
    await state.set_state(
        ProductStates.adding_category_name
    )
    await message.answer(
        "➕ Введите название категории:\n"
        "Например: Витамины",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(
    ProductStates.adding_category_name,
    F.content_type.in_(["text"])
)
async def add_category_name(
    message: Message, state: FSMContext
):
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer(
            "🚫 Отменено",
            reply_markup=admin_kb.products_admin_menu()
        )
        return
    
    await state.update_data(category_name=message.text)
    await state.set_state(
        ProductStates.adding_category_emoji
    )
    await message.answer(
        f"✅ Название: {message.text}\n\n"
        "Введите эмодзи для категории:\n"
        "Например: 💊",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(
    ProductStates.adding_category_emoji,
    F.content_type.in_(["text"])
)
async def add_category_emoji(
    message: Message, state: FSMContext
):
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer(
            "🚫 Отменено",
            reply_markup=admin_kb.products_admin_menu()
        )
        return
    
    data = await state.get_data()
    await db.add_category(
        data['category_name'], message.text
    )
    await state.clear()
    await message.answer(
        f"✅ Категория добавлена!\n\n"
        f"{message.text} {data['category_name']}",
        reply_markup=admin_kb.products_admin_menu()
    )


# ==================== ДОБАВИТЬ ПРОДУКТ ====================
@router.message(F.text == "➕ Добавить продукт")
async def add_product_start(
    message: Message, state: FSMContext
):
    if not is_admin(message):
        return
    
    categories = await db.get_categories()
    if not categories:
        await message.answer(
            "❌ Сначала добавьте категорию!\n\n"
            "Нажмите ➕ Добавить категорию",
            reply_markup=admin_kb.products_admin_menu()
        )
        return
    
    await state.set_state(
        ProductStates.adding_product_category
    )
    await message.answer(
        "➕ Выберите категорию для продукта:",
        reply_markup=admin_kb.admin_categories_keyboard(
            categories, "addprod"
        )
    )


@router.callback_query(
    ProductStates.adding_product_category,
    F.data.startswith("addprod_")
)
async def add_product_category(
    callback: CallbackQuery, state: FSMContext
):
    category_id = int(callback.data.split("_")[1])
    await state.update_data(
        product_category_id=category_id
    )
    await state.set_state(
        ProductStates.adding_product_name
    )
    await callback.message.edit_text(
        "📝 Введите название продукта:"
    )


@router.message(
    ProductStates.adding_product_name,
    F.content_type.in_(["text"])
)
async def add_product_name(
    message: Message, state: FSMContext
):
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer(
            "🚫 Отменено",
            reply_markup=admin_kb.products_admin_menu()
        )
        return
    
    await state.update_data(product_name=message.text)
    await state.set_state(
        ProductStates.adding_product_description
    )
    await message.answer(
        f"✅ Название: {message.text}\n\n"
        "📝 Введите описание продукта:",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(
    ProductStates.adding_product_description,
    F.content_type.in_(["text"])
)
async def add_product_description(
    message: Message, state: FSMContext
):
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer(
            "🚫 Отменено",
            reply_markup=admin_kb.products_admin_menu()
        )
        return
    
    await state.update_data(
        product_description=message.text
    )
    await state.set_state(
        ProductStates.adding_product_price
    )
    await message.answer(
        "💰 Введите цену продукта:\n"
        "Например: 1500 руб",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(
    ProductStates.adding_product_price,
    F.content_type.in_(["text"])
)
async def add_product_price(
    message: Message, state: FSMContext
):
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer(
            "🚫 Отменено",
            reply_markup=admin_kb.products_admin_menu()
        )
        return
    
    await state.update_data(product_price=message.text)
    await state.set_state(
        ProductStates.adding_product_photo
    )
    await message.answer(
        f"💰 Цена: {message.text}\n\n"
        "📷 Теперь отправьте фото продукта\n"
        "или нажмите кнопку ниже если фото нет:",
        reply_markup=admin_kb.skip_photo_keyboard()
    )


@router.message(
    ProductStates.adding_product_photo,
    F.content_type.in_(["photo"])
)
async def add_product_with_photo(
    message: Message, state: FSMContext
):
    """Добавляем продукт с фото"""
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    
    await db.add_product(
        category_id=data['product_category_id'],
        name=data['product_name'],
        description=data['product_description'],
        price=data['product_price'],
        photo_id=photo_id
    )
    
    await state.clear()
    await message.answer(
        f"✅ Продукт добавлен с фото!\n\n"
        f"🛍 {data['product_name']}\n"
        f"💰 {data['product_price']}",
        reply_markup=admin_kb.products_admin_menu()
    )


@router.message(
    ProductStates.adding_product_photo,
    F.content_type.in_(["text"])
)
async def add_product_without_photo(
    message: Message, state: FSMContext
):
    """Добавляем продукт без фото или отмена"""
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer(
            "🚫 Отменено",
            reply_markup=admin_kb.products_admin_menu()
        )
        return
    
    if message.text == "⏭ Пропустить фото":
        data = await state.get_data()
        
        await db.add_product(
            category_id=data['product_category_id'],
            name=data['product_name'],
            description=data['product_description'],
            price=data['product_price'],
            photo_id=None
        )
        
        await state.clear()
        await message.answer(
            f"✅ Продукт добавлен без фото!\n\n"
            f"🛍 {data['product_name']}\n"
            f"💰 {data['product_price']}",
            reply_markup=admin_kb.products_admin_menu()
        )
        return
    
    # Если прислали что-то другое
    await message.answer(
        "❌ Пожалуйста отправьте фото\n"
        "или нажмите Пропустить фото"
    )


# ==================== РЕДАКТИРОВАТЬ ПРОДУКТ ====================
@router.message(F.text == "✏ Редактировать продукт")
async def edit_product_start(
    message: Message, state: FSMContext
):
    if not is_admin(message):
        return
    
    categories = await db.get_categories()
    if not categories:
        await message.answer(
            "❌ Нет категорий и продуктов",
            reply_markup=admin_kb.products_admin_menu()
        )
        return
    
    await state.set_state(
        ProductStates.editing_product_category
    )
    await message.answer(
        "✏ Выберите категорию:",
        reply_markup=admin_kb.admin_categories_keyboard(
            categories, "editprodcat"
        )
    )


@router.callback_query(
    ProductStates.editing_product_category,
    F.data.startswith("editprodcat_")
)
async def edit_product_choose_category(
    callback: CallbackQuery, state: FSMContext
):
    category_id = int(callback.data.split("_")[1])
    products = await db.get_products_by_category(
        category_id
    )
    
    if not products:
        await callback.message.edit_text(
            "❌ В этой категории нет продуктов\n\n"
            "Выберите другую категорию",
            reply_markup=admin_kb.admin_categories_keyboard(
                await db.get_categories(), "editprodcat"
            )
        )
        return
    
    await state.set_state(
        ProductStates.editing_product_choose
    )
    await callback.message.edit_text(
        "✏ Выберите продукт для редактирования:",
        reply_markup=admin_kb.admin_products_keyboard(
            products, "editprod"
        )
    )


@router.callback_query(
    ProductStates.editing_product_choose,
    F.data.startswith("editprod_")
)
async def edit_product_enter_name(
    callback: CallbackQuery, state: FSMContext
):
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.answer("❌ Продукт не найден")
        return
    
    (prod_id, name, description, price, photo_id, category_id) = product
    
    await state.update_data(
        editing_product_id=product_id
    )
    await state.set_state(
        ProductStates.editing_product_name
    )
    await callback.message.edit_text(
        f"✏ Редактирование продукта:\n\n"
        f"📝 Текущее название: {name}\n\n"
        f"Введите новое название:"
    )


@router.message(
    ProductStates.editing_product_name,
    F.content_type.in_(["text"])
)
async def edit_product_name(
    message: Message, state: FSMContext
):
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer(
            "🚫 Отменено",
            reply_markup=admin_kb.products_admin_menu()
        )
        return
    
    await state.update_data(
        new_product_name=message.text
    )
    await state.set_state(
        ProductStates.editing_product_description
    )
    await message.answer(
        f"✅ Новое название: {message.text}\n\n"
        "📝 Введите новое описание:",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(
    ProductStates.editing_product_description,
    F.content_type.in_(["text"])
)
async def edit_product_description(
    message: Message, state: FSMContext
):
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer(
            "🚫 Отменено",
            reply_markup=admin_kb.products_admin_menu()
        )
        return
    
    await state.update_data(
        new_product_description=message.text
    )
    await state.set_state(
        ProductStates.editing_product_price
    )
    await message.answer(
        "💰 Введите новую цену:",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(
    ProductStates.editing_product_price,
    F.content_type.in_(["text"])
)
async def edit_product_price(
    message: Message, state: FSMContext
):
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer(
            "🚫 Отменено",
            reply_markup=admin_kb.products_admin_menu()
        )
        return
    
    await state.update_data(
        new_product_price=message.text
    )
    await state.set_state(
        ProductStates.editing_product_photo
    )
    await message.answer(
        f"💰 Новая цена: {message.text}\n\n"
        "📷 Отправьте новое фото продукта\n"
        "или нажмите Пропустить чтобы "
        "оставить старое фото:",
        reply_markup=admin_kb.skip_photo_keyboard()
    )


@router.message(
    ProductStates.editing_product_photo,
    F.content_type.in_(["photo"])
)
async def edit_product_new_photo(
    message: Message, state: FSMContext
):
    """Обновляем продукт с новым фото"""
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    
    await db.edit_product(
        product_id=data['editing_product_id'],
        name=data['new_product_name'],
        description=data['new_product_description'],
        price=data['new_product_price'],
        photo_id=photo_id
    )
    
    await state.clear()
    await message.answer(
        "✅ Продукт обновлён с новым фото!",
        reply_markup=admin_kb.products_admin_menu()
    )


@router.message(
    ProductStates.editing_product_photo,
    F.content_type.in_(["text"])
)
async def edit_product_keep_old_photo(
    message: Message, state: FSMContext
):
    """Оставляем старое фото или отмена"""
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer(
            "🚫 Отменено",
            reply_markup=admin_kb.products_admin_menu()
        )
        return
    
    if message.text == "⏭ Пропустить фото":
        data = await state.get_data()
        
        # Берём старое фото
        product = await db.get_product_by_id(
            data['editing_product_id']
        )
        old_photo_id = product[4] if product else None
        
        await db.edit_product(
            product_id=data['editing_product_id'],
            name=data['new_product_name'],
            description=data['new_product_description'],
            price=data['new_product_price'],
            photo_id=old_photo_id
        )
        
        await state.clear()
        await message.answer(
            "✅ Продукт обновлён!\n"
            "(фото осталось прежним)",
            reply_markup=admin_kb.products_admin_menu()
        )
        return
    
    # Если прислали что-то другое
    await message.answer(
        "❌ Пожалуйста отправьте новое фото\n"
        "или нажмите Пропустить фото"
    )


# ==================== УДАЛИТЬ ПРОДУКТ ====================
@router.message(F.text == "🗑 Удалить продукт")
async def delete_product_start(
    message: Message, state: FSMContext
):
    if not is_admin(message):
        return
    
    categories = await db.get_categories()
    if not categories:
        await message.answer(
            "❌ Нет категорий и продуктов",
            reply_markup=admin_kb.products_admin_menu()
        )
        return
    
    await state.set_state(
        ProductStates.deleting_product_category
    )
    await message.answer(
        "🗑 Выберите категорию:",
        reply_markup=admin_kb.admin_categories_keyboard(
            categories, "delprodcat"
        )
    )


@router.callback_query(
    ProductStates.deleting_product_category,
    F.data.startswith("delprodcat_")
)
async def delete_product_choose(
    callback: CallbackQuery, state: FSMContext
):
    category_id = int(callback.data.split("_")[1])
    products = await db.get_products_by_category(
        category_id
    )
    
    if not products:
        await callback.message.edit_text(
            "❌ В этой категории нет продуктов\n\n"
            "Выберите другую категорию",
            reply_markup=admin_kb.admin_categories_keyboard(
                await db.get_categories(), "delprodcat"
            )
        )
        return
    
    await state.set_state(
        ProductStates.deleting_product_choose
    )
    await callback.message.edit_text(
        "🗑 Выберите продукт для удаления:",
        reply_markup=admin_kb.admin_products_keyboard(
            products, "delprod"
        )
    )


@router.callback_query(
    ProductStates.deleting_product_choose,
    F.data.startswith("delprod_")
)
async def delete_product_confirm(
    callback: CallbackQuery, state: FSMContext
):
    product_id = int(callback.data.split("_")[1])
    await db.delete_product(product_id)
    await state.clear()
    
    await callback.message.edit_text(
        "✅ Продукт успешно удалён!"
    )
    await callback.message.answer(
        "🛍 Управление продукцией:",
        reply_markup=admin_kb.products_admin_menu()
    )


# ==================== УДАЛИТЬ КАТЕГОРИЮ ====================
@router.message(F.text == "🗑 Удалить категорию")
async def delete_category_start(
    message: Message, state: FSMContext
):
    if not is_admin(message):
        return
    
    categories = await db.get_categories()
    if not categories:
        await message.answer(
            "❌ Нет категорий для удаления",
            reply_markup=admin_kb.products_admin_menu()
        )
        return
    
    await state.set_state(
        ProductStates.deleting_category_choose
    )
    await message.answer(
        "🗑 Выберите категорию для удаления:\n\n"
        "⚠ Все продукты в этой категории "
        "тоже будут удалены!",
        reply_markup=admin_kb.admin_categories_keyboard(
            categories, "delcat"
        )
    )


@router.callback_query(
    ProductStates.deleting_category_choose,
    F.data.startswith("delcat_")
)
async def delete_category_confirm(
    callback: CallbackQuery, state: FSMContext
):
    category_id = int(callback.data.split("_")[1])
    await db.delete_category(category_id)
    await state.clear()
    
    await callback.message.edit_text(
        "✅ Категория и все её продукты удалены!"
    )
    await callback.message.answer(
        "🛍 Управление продукцией:",
        reply_markup=admin_kb.products_admin_menu()
    )


# ==================== ОТМЕНА ЧЕРЕЗ ИНЛАЙН ====================
@router.callback_query(
    F.data == "admin_cancel"
)
async def products_cancel_callback(
    callback: CallbackQuery, state: FSMContext
):
    current_state = await state.get_state()
    if current_state and "Product" in str(current_state):
        await state.clear()
        await callback.message.edit_text(
            "🚫 Отменено"
        )
        await callback.message.answer(
            "🛍 Управление продукцией:",
            reply_markup=admin_kb.products_admin_menu()
        )