from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards import admin_kb, client_kb
from config import ADMIN_ID

router = Router()


def is_admin(message: Message) -> bool:
    return message.from_user.id == ADMIN_ID


class CertStates(StatesGroup):
    waiting_photo = State()
    waiting_title = State()
    waiting_delete = State()


# ==================== КЛИЕНТ ====================

@router.message(F.text == "🏆 Сертификаты")
async def certificates_menu(message: Message):
    if is_admin(message):
        certs = await db.get_certificates()
        await message.answer(
            f"🏆 Управление сертификатами\n\n"
            f"Сертификатов в базе: {len(certs)}",
            reply_markup=admin_kb.certificates_admin_menu()
        )
        return

    await show_cert_page(message, 0)


async def show_cert_page(
    message: Message,
    index: int
):
    """Показываем сертификат по индексу"""
    certs = await db.get_certificates()

    if not certs:
        await message.answer(
            "🏆 Сертификаты пока не добавлены\n\n"
            "Загляните позже!",
            reply_markup=client_kb.back_to_menu_keyboard()
        )
        return

    total = len(certs)

    # Защита от выхода за пределы
    if index < 0:
        index = 0
    if index >= total:
        index = total - 1

    cert_id, title, photo_id = certs[index]

    await message.answer_photo(
        photo=photo_id,
        caption=(
            f"🏆 {title}\n\n"
            f"📄 {index + 1} из {total}"
        ),
        reply_markup=client_kb.certificates_keyboard(
            certs, index
        )
    )


# ==================== ЛИСТАНИЕ ====================

@router.callback_query(
    F.data.startswith("cert_page_")
)
async def navigate_cert_page(
    callback: CallbackQuery
):
    """Переключаем сертификат по индексу"""
    index = int(
        callback.data.replace("cert_page_", "")
    )
    certs = await db.get_certificates()

    if not certs:
        await callback.answer("Сертификатов нет")
        return

    total = len(certs)

    # Защита от выхода за пределы
    if index < 0:
        index = 0
    if index >= total:
        index = total - 1

    cert_id, title, photo_id = certs[index]

    try:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photo_id,
            caption=(
                f"🏆 {title}\n\n"
                f"📄 {index + 1} из {total}"
            ),
            reply_markup=client_kb.certificates_keyboard(
                certs, index
            )
        )
    except Exception as e:
        print(f"Ошибка листания: {e}")
        await callback.answer(
            "Ошибка при загрузке"
        )


# ==================== ДОБАВИТЬ СЕРТИФИКАТ ====================

@router.message(F.text == "➕ Добавить сертификат")
async def add_cert_start(
    message: Message,
    state: FSMContext
):
    if not is_admin(message):
        return
    await state.set_state(CertStates.waiting_photo)
    await message.answer(
        "📸 Отправьте фото сертификата\n\n"
        "Просто прикрепите фото к сообщению",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(CertStates.waiting_photo)
async def add_cert_get_photo(
    message: Message,
    state: FSMContext
):
    if message.text and message.text == "🚫 Отмена":
        await state.clear()
        await message.answer(
            "🚫 Отменено",
            reply_markup=admin_kb.certificates_admin_menu()
        )
        return

    if message.photo:
        photo_id = message.photo[-1].file_id
        await state.update_data(
            cert_photo_id=photo_id
        )
        await state.set_state(CertStates.waiting_title)
        await message.answer(
            "✅ Фото получено!\n\n"
            "Теперь введите название сертификата:\n"
            "Например: Сертификат дистрибьютора "
            "TIENS 2024",
            reply_markup=admin_kb.cancel_admin_keyboard()
        )
        return

    await message.answer(
        "❌ Пожалуйста отправьте ФОТО!\n\n"
        "Нажмите на 📎 скрепку → выберите фото"
    )


@router.message(CertStates.waiting_title)
async def add_cert_get_title(
    message: Message,
    state: FSMContext
):
    if message.text and message.text == "🚫 Отмена":
        await state.clear()
        await message.answer(
            "🚫 Отменено",
            reply_markup=admin_kb.certificates_admin_menu()
        )
        return

    if message.photo:
        await message.answer(
            "❌ Сейчас нужно ввести НАЗВАНИЕ текстом\n"
            "Например: Сертификат TIENS 2024"
        )
        return

    if not message.text:
        await message.answer(
            "❌ Введите название текстом"
        )
        return

    data = await state.get_data()
    photo_id = data.get('cert_photo_id')

    if not photo_id:
        await state.clear()
        await message.answer(
            "❌ Что-то пошло не так\n"
            "Попробуйте снова",
            reply_markup=admin_kb.certificates_admin_menu()
        )
        return

    await db.add_certificate(
        title=message.text,
        photo_id=photo_id
    )
    await state.clear()
    await message.answer(
        f"✅ Сертификат успешно добавлен!\n\n"
        f"🏆 {message.text}",
        reply_markup=admin_kb.certificates_admin_menu()
    )


# ==================== УДАЛИТЬ СЕРТИФИКАТ ====================

@router.message(F.text == "🗑️ Удалить сертификат")
async def delete_cert_start(
    message: Message,
    state: FSMContext
):
    if not is_admin(message):
        return

    certs = await db.get_certificates()
    if not certs:
        await message.answer(
            "❌ Нет сертификатов для удаления",
            reply_markup=admin_kb.certificates_admin_menu()
        )
        return

    await state.set_state(CertStates.waiting_delete)
    await message.answer(
        "🗑️ Выберите сертификат для удаления:",
        reply_markup=admin_kb.admin_certs_keyboard(certs)
    )


@router.callback_query(
    CertStates.waiting_delete,
    F.data.startswith("delcert_")
)
async def delete_cert_confirm(
    callback: CallbackQuery,
    state: FSMContext
):
    cert_id = int(callback.data.split("_")[1])
    await db.delete_certificate(cert_id)
    await state.clear()
    await callback.message.edit_text(
        "✅ Сертификат удалён!"
    )
    await callback.message.answer(
        "🏆 Управление сертификатами:",
        reply_markup=admin_kb.certificates_admin_menu()
    )