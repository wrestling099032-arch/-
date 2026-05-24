from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from datetime import datetime, date
import database as db
from keyboards import admin_kb, client_kb
from config import ADMIN_ID

router = Router()


def is_admin(message: Message) -> bool:
    return message.from_user.id == ADMIN_ID


class AdminStates(StatesGroup):
    # Расписание
    adding_date = State()
    adding_time_start = State()
    adding_time_end = State()
    asking_lunch = State()
    adding_lunch_start = State()
    adding_lunch_end = State()
    blocking_slot = State()
    unblocking_slot = State()
    deleting_date = State()

    # Записи
    viewing_bookings_date = State()
    canceling_booking = State()

    # Рассылка
    entering_broadcast_text = State()

    # Настройки
    editing_address = State()
    editing_contacts = State()
    editing_about = State()
    editing_prepayment_details = State()
    editing_prepayment_primary = State()
    editing_prepayment_repeated = State()

    # Социальные сети
    editing_telegram = State()
    editing_whatsapp = State()
    editing_bip = State()

    # FAQ
    adding_faq_question = State()
    adding_faq_answer = State()
    deleting_faq = State()

    # Ручное добавление
    manual_booking_name = State()
    manual_booking_age = State()
    manual_booking_phone = State()
    manual_booking_diseases = State()
    manual_booking_complaint = State()
    manual_booking_type = State()
    manual_booking_date = State()
    manual_booking_time = State()


# ==================== ВХОД В АДМИНКУ ====================

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message):
        await message.answer("❌ У вас нет доступа")
        return
    await message.answer(
        "👋 Добро пожаловать в админ панель!",
        reply_markup=admin_kb.admin_main_menu()
    )


@router.message(F.text == "🚪 Выйти из админки")
async def exit_admin(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    await state.clear()
    await message.answer(
        "👋 Вы вышли из админ панели",
        reply_markup=client_kb.main_menu(is_admin=True)
    )


# ==================== РАСПИСАНИЕ ====================

@router.message(F.text == "📋 Управление расписанием")
async def schedule_management(message: Message):
    if not is_admin(message):
        return
    await message.answer(
        "📋 Управление расписанием:",
        reply_markup=admin_kb.schedule_menu()
    )


@router.message(F.text == "➕ Добавить дату и время")
async def add_date_start(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    await state.set_state(AdminStates.adding_date)
    await message.answer(
        "📅 Введите дату в формате ДД.ММ.ГГГГ\n"
        "Например: 25.01.2025",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(AdminStates.adding_date)
async def add_date_enter(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    try:
        date_obj = datetime.strptime(message.text.strip(), "%d.%m.%Y")
        date_str = date_obj.strftime("%Y-%m-%d")
        if date_obj.date() < date.today():
            await message.answer(
                "❌ Нельзя добавить прошедшую дату\nВведите дату снова:"
            )
            return
        await state.update_data(new_date=date_str)
        await state.set_state(AdminStates.adding_time_start)
        await message.answer(
            f"✅ Дата: {message.text}\n\n"
            f"Введите время начала (ЧЧ:ММ)\nНапример: 10:00"
        )
    except ValueError:
        await message.answer(
            "❌ Неверный формат\nВведите дату в формате ДД.ММ.ГГГГ"
        )


@router.message(AdminStates.adding_time_start)
async def add_time_start(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    try:
        datetime.strptime(message.text.strip(), "%H:%M")
        await state.update_data(time_start=message.text.strip())
        await state.set_state(AdminStates.adding_time_end)
        await message.answer(
            f"✅ Начало: {message.text}\n\n"
            f"Введите время окончания (ЧЧ:ММ)\nНапример: 18:00"
        )
    except ValueError:
        await message.answer(
            "❌ Неверный формат\nВведите время в формате ЧЧ:ММ"
        )


@router.message(AdminStates.adding_time_end)
async def add_time_end(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    try:
        data = await state.get_data()
        start = datetime.strptime(data['time_start'], "%H:%M")
        end = datetime.strptime(message.text.strip(), "%H:%M")
        if end <= start:
            await message.answer(
                "❌ Время окончания должно быть позже начала\nВведите снова:"
            )
            return
        await state.update_data(time_end=message.text.strip())
        await state.set_state(AdminStates.asking_lunch)
        await message.answer(
            f"✅ Окончание: {message.text}\n\n🍽 Добавить перерыв на обед?",
            reply_markup=admin_kb.lunch_keyboard()
        )
    except ValueError:
        await message.answer(
            "❌ Неверный формат\nВведите время в формате ЧЧ:ММ"
        )


@router.message(AdminStates.asking_lunch)
async def asking_lunch(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    if message.text == "❌ Нет без обеда":
        data = await state.get_data()
        slots_count = await db.add_schedule_slots(
            data['new_date'], data['time_start'], data['time_end']
        )
        d = data['new_date'].split("-")
        date_pretty = f"{d[2]}.{d[1]}.{d[0]}"
        await state.clear()
        await message.answer(
            f"✅ Расписание добавлено!\n\n"
            f"📅 Дата: {date_pretty}\n"
            f"🕐 С {data['time_start']} до {data['time_end']}\n"
            f"📋 Слотов по 20 мин: {slots_count}",
            reply_markup=admin_kb.schedule_menu()
        )
    elif message.text == "✅ Да добавить обед":
        await state.set_state(AdminStates.adding_lunch_start)
        await message.answer(
            "🍽 Введите время начала обеда (ЧЧ:ММ)\nНапример: 13:00",
            reply_markup=admin_kb.cancel_admin_keyboard()
        )


@router.message(AdminStates.adding_lunch_start)
async def add_lunch_start(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    try:
        datetime.strptime(message.text.strip(), "%H:%M")
        await state.update_data(lunch_start=message.text.strip())
        await state.set_state(AdminStates.adding_lunch_end)
        await message.answer(
            f"✅ Начало обеда: {message.text}\n\n"
            f"Введите время окончания обеда (ЧЧ:ММ)\nНапример: 14:00"
        )
    except ValueError:
        await message.answer(
            "❌ Неверный формат\nВведите время в формате ЧЧ:ММ"
        )


@router.message(AdminStates.adding_lunch_end)
async def add_lunch_end(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    try:
        data = await state.get_data()
        lunch_s = datetime.strptime(data['lunch_start'], "%H:%M")
        lunch_e = datetime.strptime(message.text.strip(), "%H:%M")
        if lunch_e <= lunch_s:
            await message.answer(
                "❌ Конец обеда должен быть позже начала"
            )
            return
        slots_count = await db.add_schedule_slots(
            data['new_date'], data['time_start'], data['time_end'],
            data['lunch_start'], message.text.strip()
        )
        d = data['new_date'].split("-")
        date_pretty = f"{d[2]}.{d[1]}.{d[0]}"
        await state.clear()
        await message.answer(
            f"✅ Расписание добавлено!\n\n"
            f"📅 Дата: {date_pretty}\n"
            f"🕐 С {data['time_start']} до {data['time_end']}\n"
            f"🍽 Обед: {data['lunch_start']} — {message.text.strip()}\n"
            f"📋 Рабочих слотов: {slots_count}",
            reply_markup=admin_kb.schedule_menu()
        )
    except ValueError:
        await message.answer(
            "❌ Неверный формат\nВведите время в формате ЧЧ:ММ"
        )


# ==================== ПРОСМОТР РАСПИСАНИЯ ====================

@router.message(F.text == "👁 Посмотреть расписание")
async def view_schedule(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    # Сбрасываем состояние чтобы не было конфликтов
    await state.clear()
    dates = await db.get_all_dates_admin()
    if not dates:
        await message.answer(
            "📭 Расписание пусто",
            reply_markup=admin_kb.schedule_menu()
        )
        return
    await message.answer(
        "📅 Выберите дату для просмотра:",
        reply_markup=admin_kb.admin_dates_keyboard(dates, action="view_date")
    )


@router.callback_query(F.data.startswith("view_date_"))
async def view_date_slots(callback: CallbackQuery, state: FSMContext):
    """
    Показываем расписание + записи клиентов на выбранную дату
    callback_data: view_date_{YYYY-MM-DD}
    """
    await state.clear()
    selected_date = callback.data.replace("view_date_", "")

    # Проверка формата
    try:
        datetime.strptime(selected_date, "%Y-%m-%d")
    except ValueError:
        await callback.answer("❌ Неверный формат даты", show_alert=True)
        return

    d = selected_date.split("-")
    date_pretty = f"{d[2]}.{d[1]}.{d[0]}"

    # Получаем слоты расписания
    slots = await db.get_slots_by_date(selected_date)

    # Получаем записи клиентов на эту дату
    bookings = await db.get_bookings_by_date(selected_date)

    # Строим словарь: время -> запись клиента
    bookings_by_time = {}
    for b in bookings:
        b_id, name, age, phone, diseases, complaint, client_type, btime, status = b
        bookings_by_time[btime] = {
            "id": b_id,
            "name": name,
            "age": age,
            "phone": phone,
            "client_type": client_type,
            "status": status,
        }

    text = f"📅 Расписание на {date_pretty}:\n\n"
    text += "🟢 свободно | 🔴 занято\n⛔ заблокировано | 🍽 обед\n\n"

    if not slots:
        text += "Слотов нет"
    else:
        for slot_time, status in slots:
            if status == "free":
                text += f"🟢 {slot_time} — свободно\n"
            elif status == "lunch":
                text += f"🍽 {slot_time} — обед\n"
            elif status == "blocked":
                text += f"⛔ {slot_time} — заблокировано\n"
            elif status == "booked":
                if slot_time in bookings_by_time:
                    b = bookings_by_time[slot_time]
                    type_text = (
                        "Первичка"
                        if b["client_type"] == "primary"
                        else "Повторник"
                    )
                    status_text = {
                        "pending": "⏳ Ожидает",
                        "approved": "✅ Одобрена",
                        "rejected": "❌ Отклонена"
                    }.get(b["status"], b["status"])
                    text += (
                        f"🔴 {slot_time} — {type_text}\n"
                        f"   👤 {b['name']}, {b['age']} лет\n"
                        f"   📞 {b['phone']}\n"
                        f"   {status_text} | ID: {b['id']}\n"
                    )
                else:
                    text += f"🔴 {slot_time} — занято\n"

    if bookings:
        text += f"\n📊 Всего записей: {len(bookings)}"

    if len(text) > 4000:
        text = text[:3900] + "\n\n...список обрезан"

    dates = await db.get_all_dates_admin()
    try:
        await callback.message.edit_text(
            text,
            reply_markup=admin_kb.admin_dates_keyboard(dates, action="view_date")
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=admin_kb.admin_dates_keyboard(dates, action="view_date")
        )
    await callback.answer()


# ==================== БЛОКИРОВКА ====================

@router.message(F.text == "🔒 Заблокировать слот")
async def block_slot_start(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    dates = await db.get_all_dates_admin()
    if not dates:
        await message.answer("📭 Нет доступных дат")
        return
    await state.set_state(AdminStates.blocking_slot)
    await message.answer(
        "📅 Выберите дату:",
        reply_markup=admin_kb.admin_dates_keyboard(dates, action="block_date")
    )


@router.callback_query(AdminStates.blocking_slot, F.data.startswith("block_date_"))
async def block_slot_choose_time(callback: CallbackQuery, state: FSMContext):
    selected_date = callback.data.replace("block_date_", "")
    slots = await db.get_slots_by_date(selected_date)
    free_slots = [(t, s) for t, s in slots if s == "free"]
    if not free_slots:
        await callback.message.edit_text(
            "❌ Нет свободных слотов на эту дату"
        )
        await callback.answer()
        return
    await callback.message.edit_text(
        "🔒 Выберите время для блокировки:",
        reply_markup=admin_kb.admin_slots_keyboard(
            free_slots, selected_date, "blockslot"
        )
    )
    await callback.answer()


@router.callback_query(F.data.startswith("blockslot|"))
async def block_slot_confirm(callback: CallbackQuery, state: FSMContext):
    # Формат: blockslot|{date}|{time}
    parts = callback.data.split("|")
    selected_date = parts[1]
    time_str = parts[2]

    await db.update_slot_status(selected_date, time_str, "blocked")
    await state.clear()
    d = selected_date.split("-")
    date_pretty = f"{d[2]}.{d[1]}.{d[0]}"
    await callback.message.edit_text(
        f"⛔ Слот {time_str} на {date_pretty} заблокирован"
    )
    await callback.message.answer(
        "📋 Управление расписанием:",
        reply_markup=admin_kb.schedule_menu()
    )
    await callback.answer()


# ==================== РАЗБЛОКИРОВКА ====================

@router.message(F.text == "🔓 Разблокировать слот")
async def unblock_slot_start(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    dates = await db.get_all_dates_admin()
    if not dates:
        await message.answer("📭 Нет доступных дат")
        return
    await state.set_state(AdminStates.unblocking_slot)
    await message.answer(
        "📅 Выберите дату:",
        reply_markup=admin_kb.admin_dates_keyboard(dates, action="unblock_date")
    )


@router.callback_query(AdminStates.unblocking_slot, F.data.startswith("unblock_date_"))
async def unblock_slot_choose_time(callback: CallbackQuery, state: FSMContext):
    selected_date = callback.data.replace("unblock_date_", "")
    slots = await db.get_slots_by_date(selected_date)
    blocked = [(t, s) for t, s in slots if s == "blocked"]
    if not blocked:
        await callback.message.edit_text("❌ Нет заблокированных слотов")
        await callback.answer()
        return
    await callback.message.edit_text(
        "🔓 Выберите время для разблокировки:",
        reply_markup=admin_kb.admin_slots_keyboard(
            blocked, selected_date, "unblockslot"
        )
    )
    await callback.answer()


@router.callback_query(F.data.startswith("unblockslot|"))
async def unblock_slot_confirm(callback: CallbackQuery, state: FSMContext):
    # Формат: unblockslot|{date}|{time}
    parts = callback.data.split("|")
    selected_date = parts[1]
    time_str = parts[2]

    await db.update_slot_status(selected_date, time_str, "free")
    await state.clear()
    d = selected_date.split("-")
    date_pretty = f"{d[2]}.{d[1]}.{d[0]}"
    await callback.message.edit_text(
        f"🔓 Слот {time_str} на {date_pretty} разблокирован"
    )
    await callback.message.answer(
        "📋 Управление расписанием:",
        reply_markup=admin_kb.schedule_menu()
    )
    await callback.answer()


# ==================== УДАЛЕНИЕ ДАТЫ ====================

@router.message(F.text == "🗑 Удалить дату")
async def delete_date_start(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    dates = await db.get_all_dates_admin()
    if not dates:
        await message.answer("📭 Нет дат для удаления")
        return
    await state.set_state(AdminStates.deleting_date)
    await message.answer(
        "🗑 Выберите дату для удаления:",
        reply_markup=admin_kb.admin_dates_keyboard(dates, action="delete_date")
    )


@router.callback_query(AdminStates.deleting_date, F.data.startswith("delete_date_"))
async def delete_date_confirm(callback: CallbackQuery, state: FSMContext):
    selected_date = callback.data.replace("delete_date_", "")
    d = selected_date.split("-")
    date_pretty = f"{d[2]}.{d[1]}.{d[0]}"
    await db.delete_date(selected_date)
    await state.clear()
    await callback.message.edit_text(f"✅ Дата {date_pretty} удалена!")
    await callback.message.answer(
        "📋 Управление расписанием:",
        reply_markup=admin_kb.schedule_menu()
    )
    await callback.answer()


# ==================== ЗАПИСИ ====================

@router.message(F.text == "📝 Записи клиентов")
async def bookings_management(message: Message):
    if not is_admin(message):
        return
    await message.answer(
        "📝 Записи клиентов:",
        reply_markup=admin_kb.bookings_menu()
    )


@router.message(F.text == "📅 Записи на сегодня")
async def bookings_today(message: Message):
    if not is_admin(message):
        return
    today = date.today().strftime("%Y-%m-%d")
    bookings = await db.get_bookings_by_date(today)
    today_pretty = date.today().strftime("%d.%m.%Y")
    if not bookings:
        await message.answer(
            f"📭 На сегодня ({today_pretty}) записей нет",
            reply_markup=admin_kb.bookings_menu()
        )
        return
    text = f"📅 Записи на {today_pretty}:\n\n"
    for b in bookings:
        b_id, name, age, phone, diseases, complaint, client_type, btime, status = b
        type_text = "🔵 Первичка" if client_type == "primary" else "🟢 Повторник"
        status_text = {
            "pending": "⏳ Ожидает",
            "approved": "✅ Одобрена",
            "rejected": "❌ Отклонена"
        }.get(status, status)
        text += (
            f"🕐 {btime} | {type_text}\n"
            f"👤 {name}, {age} лет\n"
            f"📞 {phone}\n"
            f"🏥 Хрон. болезни: {diseases}\n"
            f"💬 {complaint}\n"
            f"Статус: {status_text}\n"
            f"ID: {b_id}\n"
            f"{'—' * 20}\n"
        )
    if len(text) > 4000:
        text = text[:3900] + "\n\n...список обрезан"
    await message.answer(text, reply_markup=admin_kb.bookings_menu())


@router.message(F.text == "🗓 Записи на другую дату")
async def bookings_other_date(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    dates = await db.get_all_dates_admin()
    if not dates:
        await message.answer(
            "📭 Нет дат в расписании",
            reply_markup=admin_kb.bookings_menu()
        )
        return
    await state.set_state(AdminStates.viewing_bookings_date)
    await message.answer(
        "📅 Выберите дату:",
        reply_markup=admin_kb.admin_dates_keyboard(dates, action="bookings_date")
    )


@router.callback_query(
    AdminStates.viewing_bookings_date,
    F.data.startswith("bookings_date_")
)
async def show_bookings_by_date_callback(callback: CallbackQuery, state: FSMContext):
    selected_date = callback.data.replace("bookings_date_", "")
    d = selected_date.split("-")
    date_pretty = f"{d[2]}.{d[1]}.{d[0]}"
    bookings = await db.get_bookings_by_date(selected_date)
    await state.clear()

    if not bookings:
        await callback.message.edit_text(f"📭 На {date_pretty} записей нет")
        await callback.message.answer(
            "📝 Записи клиентов:",
            reply_markup=admin_kb.bookings_menu()
        )
        await callback.answer()
        return

    text = f"📅 Записи на {date_pretty}:\n\n"
    for b in bookings:
        b_id, name, age, phone, diseases, complaint, client_type, btime, status = b
        type_text = "🔵 Первичка" if client_type == "primary" else "🟢 Повторник"
        status_text = {
            "pending": "⏳ Ожидает",
            "approved": "✅ Одобрена",
            "rejected": "❌ Отклонена"
        }.get(status, status)
        text += (
            f"🕐 {btime} | {type_text}\n"
            f"👤 {name}, {age} лет\n"
            f"📞 {phone}\n"
            f"🏥 {diseases}\n"
            f"💬 {complaint}\n"
            f"{status_text}\n"
            f"ID: {b_id}\n"
            f"{'—' * 20}\n"
        )

    if len(text) > 4000:
        text = text[:3900] + "\n\n...список обрезан"

    await callback.message.edit_text(text)
    await callback.message.answer(
        "📝 Записи клиентов:",
        reply_markup=admin_kb.bookings_menu()
    )
    await callback.answer()


@router.message(F.text == "❌ Отменить запись клиента")
async def cancel_client_booking_start(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    await state.set_state(AdminStates.canceling_booking)
    await message.answer(
        "❌ Введите ID записи для отмены\n\nID виден в списке записей",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(AdminStates.canceling_booking)
async def cancel_client_booking(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    if not message.text.isdigit():
        await message.answer("❌ Введите числовой ID записи")
        return
    booking_id = int(message.text)
    user_id = await db.cancel_booking(booking_id)
    if not user_id:
        await message.answer(
            "❌ Запись с таким ID не найдена",
            reply_markup=admin_kb.bookings_menu()
        )
        await state.clear()
        return
    await state.clear()
    await message.answer(
        f"✅ Запись #{booking_id} отменена",
        reply_markup=admin_kb.bookings_menu()
    )
    try:
        await message.bot.send_message(
            user_id,
            "❌ Ваша запись была отменена\n\nСвяжитесь с нами для переноса",
            reply_markup=client_kb.main_menu()
        )
    except Exception:
        pass


# ==================== РАССЫЛКА ====================

@router.message(F.text == "📢 Рассылка")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    await state.set_state(AdminStates.entering_broadcast_text)
    await message.answer(
        "📢 Что хотите отправить?\n\n"
        "✏️ Просто напишите текст\n"
        "📷 Или отправьте фото с подписью\n\n"
        "Если фото — добавьте подпись (текст под фото при отправке)",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(AdminStates.entering_broadcast_text, F.content_type.in_(["photo"]))
async def broadcast_with_photo(message: Message, state: FSMContext):
    if not message.caption:
        await message.answer(
            "❌ Добавьте подпись к фото!\n\n"
            "Когда отправляете фото — напишите текст под ним"
        )
        return
    photo_id = message.photo[-1].file_id
    caption = message.caption
    users = await db.get_all_users()
    await state.clear()
    await message.answer("⏳ Начинаю рассылку...")
    success, failed = 0, 0
    for user_id in users:
        try:
            await message.bot.send_photo(
                chat_id=user_id,
                photo=photo_id,
                caption=f"📢 Сообщение от TIENS Черкесск:\n\n{caption}"
            )
            success += 1
        except Exception:
            failed += 1
    await message.answer(
        f"✅ Рассылка с фото завершена!\n\n"
        f"📤 Отправлено: {success}\n"
        f"❌ Не доставлено: {failed}",
        reply_markup=admin_kb.admin_main_menu()
    )


@router.message(AdminStates.entering_broadcast_text, F.content_type.in_(["text"]))
async def broadcast_text_only(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    users = await db.get_all_users()
    await state.clear()
    await message.answer("⏳ Начинаю рассылку...")
    success, failed = 0, 0
    for user_id in users:
        try:
            await message.bot.send_message(
                chat_id=user_id,
                text=f"📢 Сообщение от TIENS Черкесск:\n\n{message.text}"
            )
            success += 1
        except Exception:
            failed += 1
    await message.answer(
        f"✅ Рассылка завершена!\n\n"
        f"📤 Отправлено: {success}\n"
        f"❌ Не доставлено: {failed}",
        reply_markup=admin_kb.admin_main_menu()
    )


# ==================== СТАТИСТИКА ====================

@router.message(F.text == "📊 Статистика")
async def show_statistics(message: Message):
    if not is_admin(message):
        return
    users_count = await db.get_users_count()
    bookings_count = await db.get_bookings_count()
    today = date.today().strftime("%Y-%m-%d")
    today_bookings = await db.get_bookings_by_date(today)
    await message.answer(
        f"📊 Статистика бота:\n\n"
        f"👥 Всего пользователей: {users_count}\n"
        f"✅ Одобренных записей: {bookings_count}\n"
        f"📅 Записей на сегодня: {len(today_bookings)}",
        reply_markup=admin_kb.admin_main_menu()
    )


# ==================== НАСТРОЙКИ ====================

@router.message(F.text == "⚙️ Настройки")
async def settings(message: Message):
    if not is_admin(message):
        return
    await message.answer("⚙️ Настройки:", reply_markup=admin_kb.settings_menu())


@router.message(F.text == "📍 Изменить адрес")
async def edit_address(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    current = await db.get_setting("address")
    await state.set_state(AdminStates.editing_address)
    await message.answer(
        f"📍 Текущий адрес:\n{current}\n\nВведите новый адрес:",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(AdminStates.editing_address)
async def save_address(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    await db.update_setting("address", message.text)
    await state.clear()
    await message.answer("✅ Адрес обновлён!", reply_markup=admin_kb.settings_menu())


@router.message(F.text == "📞 Изменить контакты")
async def edit_contacts(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    current = await db.get_setting("contacts")
    await state.set_state(AdminStates.editing_contacts)
    await message.answer(
        f"📞 Текущие контакты:\n{current}\n\nВведите новые контакты:",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(AdminStates.editing_contacts)
async def save_contacts(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    await db.update_setting("contacts", message.text)
    await state.clear()
    await message.answer(
        "✅ Контакты обновлены!",
        reply_markup=admin_kb.settings_menu()
    )


@router.message(F.text == "📝 Изменить текст о тестировании")
async def edit_about(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    current = await db.get_setting("about_testing")
    await state.set_state(AdminStates.editing_about)
    await message.answer(
        f"📝 Текущий текст:\n{current}\n\nВведите новый текст:",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(AdminStates.editing_about)
async def save_about(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    await db.update_setting("about_testing", message.text)
    await state.clear()
    await message.answer(
        "✅ Текст о тестировании обновлён!",
        reply_markup=admin_kb.settings_menu()
    )


@router.message(F.text == "💳 Изменить реквизиты оплаты")
async def edit_prepayment(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    current = await db.get_setting("prepayment_details")
    await state.set_state(AdminStates.editing_prepayment_details)
    await message.answer(
        f"💳 Текущие реквизиты:\n{current}\n\nВведите новые реквизиты:",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(AdminStates.editing_prepayment_details)
async def save_prepayment(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    await db.update_setting("prepayment_details", message.text)
    await state.clear()
    await message.answer(
        "✅ Реквизиты обновлены!",
        reply_markup=admin_kb.settings_menu()
    )


# ==================== СУММЫ ПРЕДОПЛАТ ====================

@router.message(F.text == "💰 Изменить суммы предоплат")
async def edit_prepayment_amounts(message: Message):
    if not is_admin(message):
        return
    primary = await db.get_setting("prepayment_primary")
    repeated = await db.get_setting("prepayment_repeated")
    await message.answer(
        f"💰 Текущие суммы предоплат:\n\n"
        f"🔵 Первичка: {primary} руб\n"
        f"🟢 Повторник: {repeated} руб\n\n"
        f"Что изменить?",
        reply_markup=admin_kb.prepayment_amounts_menu()
    )


@router.message(F.text == "🔵 Сумма для первички")
async def edit_primary_amount(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    current = await db.get_setting("prepayment_primary")
    await state.set_state(AdminStates.editing_prepayment_primary)
    await message.answer(
        f"🔵 Текущая сумма для первички: {current} руб\n\n"
        f"Введите новую сумму (только цифры):",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(AdminStates.editing_prepayment_primary)
async def save_primary_amount(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    if not message.text.isdigit():
        await message.answer("❌ Введите только цифры\nНапример: 1500")
        return
    await db.update_setting("prepayment_primary", message.text)
    await state.clear()
    await message.answer(
        f"✅ Сумма для первички: {message.text} руб",
        reply_markup=admin_kb.settings_menu()
    )


@router.message(F.text == "🟢 Сумма для повторника")
async def edit_repeated_amount(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    current = await db.get_setting("prepayment_repeated")
    await state.set_state(AdminStates.editing_prepayment_repeated)
    await message.answer(
        f"🟢 Текущая сумма для повторника: {current} руб\n\n"
        f"Введите новую сумму (только цифры):",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(AdminStates.editing_prepayment_repeated)
async def save_repeated_amount(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    if not message.text.isdigit():
        await message.answer("❌ Введите только цифры\nНапример: 500")
        return
    await db.update_setting("prepayment_repeated", message.text)
    await state.clear()
    await message.answer(
        f"✅ Сумма для повторника: {message.text} руб",
        reply_markup=admin_kb.settings_menu()
    )


# ==================== СОЦИАЛЬНЫЕ СЕТИ ====================

@router.message(F.text == "🌐 Социальные сети")
async def socials_settings(message: Message):
    if not is_admin(message):
        return
    socials = await db.get_social_links()
    text = "🌐 Текущие соц сети:\n\n"
    for s_id, name, url in socials:
        text += f"• {name}: {url}\n"
    await message.answer(text, reply_markup=admin_kb.socials_menu())


@router.message(F.text == "✈️ Изменить Telegram")
async def edit_telegram(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    await state.set_state(AdminStates.editing_telegram)
    await message.answer(
        "✈️ Введите ссылку на Telegram\nНапример: https://t.me/username",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(AdminStates.editing_telegram)
async def save_telegram(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    await db.update_social_link("Telegram", message.text)
    await state.clear()
    await message.answer("✅ Telegram обновлён!", reply_markup=admin_kb.socials_menu())


@router.message(F.text == "📱 Изменить WhatsApp")
async def edit_whatsapp(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    await state.set_state(AdminStates.editing_whatsapp)
    await message.answer(
        "📱 Введите ссылку на WhatsApp\nНапример: https://wa.me/79281234567",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(AdminStates.editing_whatsapp)
async def save_whatsapp(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    await db.update_social_link("WhatsApp", message.text)
    await state.clear()
    await message.answer("✅ WhatsApp обновлён!", reply_markup=admin_kb.socials_menu())


@router.message(F.text == "💬 Изменить BIP")
async def edit_bip(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    await state.set_state(AdminStates.editing_bip)
    await message.answer(
        "💬 Введите ссылку на BIP\nНапример: https://bip.to/username",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(AdminStates.editing_bip)
async def save_bip(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    await db.update_social_link("BIP", message.text)
    await state.clear()
    await message.answer("✅ BIP обновлён!", reply_markup=admin_kb.socials_menu())


# ==================== РЕЗУЛЬТАТЫ ПРОГРАММ ====================

@router.message(F.text == "⭐ Редактировать результаты")
async def edit_results(message: Message):
    if not is_admin(message):
        return
    faqs = await db.get_faq()
    if not faqs:
        await message.answer(
            "📭 Результатов пока нет\n\nНажмите ➕ Добавить результат",
            reply_markup=admin_kb.faq_admin_menu()
        )
        return
    text = "⭐ Текущие результаты:\n\n"
    for faq_id, question, answer in faqs:
        text += f"🔹 ID: {faq_id}\n❓ {question}\n💬 {answer}\n{'—' * 20}\n"
    if len(text) > 4000:
        parts_list, current = [], ""
        for line in text.split("\n"):
            if len(current) + len(line) > 4000:
                parts_list.append(current)
                current = line + "\n"
            else:
                current += line + "\n"
        if current:
            parts_list.append(current)
        for i, part in enumerate(parts_list):
            if i == len(parts_list) - 1:
                await message.answer(part, reply_markup=admin_kb.faq_admin_menu())
            else:
                await message.answer(part)
    else:
        await message.answer(text, reply_markup=admin_kb.faq_admin_menu())


@router.message(F.text == "👁 Посмотреть все результаты")
async def view_all_results(message: Message):
    if not is_admin(message):
        return
    await edit_results(message)


@router.message(F.text == "➕ Добавить результат")
async def add_result_start(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    await state.set_state(AdminStates.adding_faq_question)
    await message.answer(
        "📝 Введите заголовок результата:\n\nНапример: Похудение за 3 месяца",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(AdminStates.adding_faq_question)
async def add_result_question(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer("🚫 Отменено", reply_markup=admin_kb.faq_admin_menu())
        return
    await state.update_data(faq_question=message.text)
    await state.set_state(AdminStates.adding_faq_answer)
    await message.answer(
        f"✅ Заголовок: {message.text}\n\n📝 Теперь введите описание результата:",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(AdminStates.adding_faq_answer)
async def add_result_answer(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer("🚫 Отменено", reply_markup=admin_kb.faq_admin_menu())
        return
    data = await state.get_data()
    await db.add_faq(data['faq_question'], message.text)
    await state.clear()
    await message.answer("✅ Результат добавлен!", reply_markup=admin_kb.faq_admin_menu())


@router.message(F.text == "🗑 Удалить результат")
async def delete_result_start(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    faqs = await db.get_faq()
    if not faqs:
        await message.answer(
            "❌ Нет результатов для удаления",
            reply_markup=admin_kb.faq_admin_menu()
        )
        return
    text = "🗑 Результаты для удаления:\n\n"
    for faq_id, question, answer in faqs:
        text += f"🔹 ID: {faq_id} — {question}\n"
    await state.set_state(AdminStates.deleting_faq)
    await message.answer(
        text + "\n\nВведите ID результата который хотите удалить:",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(AdminStates.deleting_faq)
async def delete_result_confirm(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer("🚫 Отменено", reply_markup=admin_kb.faq_admin_menu())
        return
    if not message.text.isdigit():
        await message.answer("❌ Введите числовой ID\n\nНапример: 1")
        return
    faq_id = int(message.text)
    await db.delete_faq(faq_id)
    await state.clear()
    await message.answer(
        f"✅ Результат #{faq_id} удалён!",
        reply_markup=admin_kb.faq_admin_menu()
    )


# ==================== НАВИГАЦИЯ ====================

@router.message(F.text == "🔙 Назад в настройки")
async def back_to_settings(message: Message):
    if not is_admin(message):
        return
    await message.answer("⚙️ Настройки:", reply_markup=admin_kb.settings_menu())


@router.message(F.text == "🔙 Назад в админку")
async def back_to_admin(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    await state.clear()
    await message.answer("👋 Админ панель:", reply_markup=admin_kb.admin_main_menu())


# ==================== РУЧНОЕ ДОБАВЛЕНИЕ ====================

@router.message(F.text == "➕ Добавить запись вручную")
async def manual_booking_start(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    await state.set_state(AdminStates.manual_booking_name)
    await message.answer(
        "➕ Добавление записи вручную\n\nВведите имя и фамилию клиента:",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(AdminStates.manual_booking_name)
async def manual_booking_get_name(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    await state.update_data(manual_name=message.text)
    await state.set_state(AdminStates.manual_booking_age)
    await message.answer(f"👤 Имя: {message.text}\n\nВведите возраст клиента:")


@router.message(AdminStates.manual_booking_age)
async def manual_booking_get_age(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    if not message.text.isdigit():
        await message.answer("❌ Введите возраст цифрами")
        return
    await state.update_data(manual_age=int(message.text))
    await state.set_state(AdminStates.manual_booking_phone)
    await message.answer(f"🎂 Возраст: {message.text}\n\nВведите номер телефона:")


@router.message(AdminStates.manual_booking_phone)
async def manual_booking_get_phone(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    await state.update_data(manual_phone=message.text)
    await state.set_state(AdminStates.manual_booking_diseases)
    await message.answer(
        f"📞 Телефон: {message.text}\n\nЕсть хронические заболевания?",
        reply_markup=admin_kb.manual_yes_no_keyboard()
    )


@router.message(AdminStates.manual_booking_diseases)
async def manual_booking_get_diseases(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    if message.text not in ["✅ Да", "❌ Нет"]:
        await message.answer(
            "Нажмите ✅ Да или ❌ Нет",
            reply_markup=admin_kb.manual_yes_no_keyboard()
        )
        return
    has_diseases = "Да" if message.text == "✅ Да" else "Нет"
    await state.update_data(manual_diseases=has_diseases)
    await state.set_state(AdminStates.manual_booking_complaint)
    await message.answer(
        f"🏥 Хрон. болезни: {has_diseases}\n\nВведите цель визита или жалобу:",
        reply_markup=admin_kb.cancel_admin_keyboard()
    )


@router.message(AdminStates.manual_booking_complaint)
async def manual_booking_get_complaint(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    await state.update_data(manual_complaint=message.text)
    await state.set_state(AdminStates.manual_booking_type)
    await message.answer(
        f"💬 Жалоба: {message.text}\n\nВыберите тип клиента:",
        reply_markup=admin_kb.manual_booking_type_keyboard()
    )


@router.message(AdminStates.manual_booking_type)
async def manual_booking_get_type(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await cancel_admin(message, state)
        return
    if message.text not in ["🔵 Первичка (40 мин)", "🟢 Повторник (20 мин)"]:
        await message.answer(
            "Выберите тип из кнопок",
            reply_markup=admin_kb.manual_booking_type_keyboard()
        )
        return
    client_type = "primary" if "Первичка" in message.text else "repeated"
    await state.update_data(manual_type=client_type)
    await state.set_state(AdminStates.manual_booking_date)

    dates = await db.get_all_dates_admin()
    if not dates:
        await message.answer(
            "❌ Нет дат в расписании\n\nСначала добавьте дату!",
            reply_markup=admin_kb.bookings_menu()
        )
        await state.clear()
        return
    await message.answer(
        "📅 Выберите дату:",
        reply_markup=admin_kb.admin_dates_keyboard(dates, action="manual_date")
    )


@router.callback_query(
    AdminStates.manual_booking_date,
    F.data.startswith("manual_date_")
)
async def manual_booking_get_date(callback: CallbackQuery, state: FSMContext):
    selected_date = callback.data.replace("manual_date_", "")
    await state.update_data(manual_date=selected_date)

    data = await state.get_data()
    client_type = data.get("manual_type", "primary")

    if client_type == "primary":
        times = await db.get_free_slots_for_primary(selected_date)
    else:
        times = await db.get_free_slots_for_repeated(selected_date)

    if not times:
        await callback.message.edit_text(
            "❌ Нет свободных слотов на эту дату\n\nВыберите другую дату:",
            reply_markup=admin_kb.admin_dates_keyboard(
                await db.get_all_dates_admin(), action="manual_date"
            )
        )
        await callback.answer()
        return

    await state.set_state(AdminStates.manual_booking_time)
    await callback.message.edit_text(
        "🕐 Выберите время:",
        reply_markup=admin_kb.admin_slots_keyboard(
            [(t, "free") for t in times], selected_date, "manualtime"
        )
    )
    await callback.answer()


@router.callback_query(
    AdminStates.manual_booking_time,
    F.data.startswith("manualtime|")
)
async def manual_booking_get_time(callback: CallbackQuery, state: FSMContext):
    """
    Формат callback_data: manualtime|{date}|{time}
    Например: manualtime|2025-01-25|10:00
    Парсим через split("|") — безопасно для любых дат и времён
    """
    parts = callback.data.split("|")
    selected_date = parts[1]  # 2025-01-25
    time_str = parts[2]       # 10:00

    data = await state.get_data()
    client_type = data.get("manual_type", "primary")

    d = selected_date.split("-")
    date_pretty = f"{d[2]}.{d[1]}.{d[0]}"
    type_text = "🔵 Первичка" if client_type == "primary" else "🟢 Повторник"

    await db.add_manual_booking(
        client_name=data['manual_name'],
        client_age=data['manual_age'],
        client_phone=data['manual_phone'],
        has_diseases=data['manual_diseases'],
        complaint=data['manual_complaint'],
        client_type=client_type,
        date=selected_date,
        time=time_str
    )
    await state.clear()
    await callback.message.edit_text(
        f"✅ Запись добавлена!\n\n"
        f"👤 {data['manual_name']}\n"
        f"📅 {date_pretty}\n"
        f"🕐 {time_str}\n"
        f"Тип: {type_text}\n"
        f"📞 {data['manual_phone']}"
    )
    await callback.message.answer(
        "📝 Записи клиентов:",
        reply_markup=admin_kb.bookings_menu()
    )
    await callback.answer()


# ==================== ОТМЕНА ====================

async def cancel_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🚫 Отменено", reply_markup=admin_kb.admin_main_menu())


@router.callback_query(F.data == "admin_cancel")
async def admin_cancel_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🚫 Отменено")
    await callback.message.answer(
        "👋 Админ панель:",
        reply_markup=admin_kb.admin_main_menu()
    )
    await callback.answer()