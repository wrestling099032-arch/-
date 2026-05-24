from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards import client_kb, admin_kb
from config import ADMIN_ID

router = Router()


class BookingStates(StatesGroup):
    choosing_type = State()
    choosing_date = State()
    choosing_time = State()
    entering_name = State()
    entering_age = State()
    entering_phone = State()
    entering_diseases = State()
    entering_complaint = State()
    confirming = State()


# ==================== НАЧАЛО ЗАПИСИ ====================

@router.message(F.text == "📅 Записаться на тестирование")
async def start_booking(message: Message, state: FSMContext):
    await state.set_state(BookingStates.choosing_type)
    await message.answer(
        "👋 Вы записываетесь впервые или уже были?\n\n"
        "🆕 Первичка — 40 минут — предоплата 1500 руб\n"
        "🔄 Повторник — 20 минут — предоплата 500 руб",
        reply_markup=client_kb.client_type_keyboard()
    )


# ==================== ВЫБОР ТИПА ====================

@router.message(
    BookingStates.choosing_type,
    F.text.in_([
        "🆕 Первый раз (первичка)",
        "🔄 Уже был(а) (повторник)"
    ])
)
async def choose_client_type(
    message: Message,
    state: FSMContext
):
    if message.text == "🆕 Первый раз (первичка)":
        client_type = "primary"
        prepayment = await db.get_setting(
            "prepayment_primary"
        )
        duration = "40 минут"
    else:
        client_type = "repeated"
        prepayment = await db.get_setting(
            "prepayment_repeated"
        )
        duration = "20 минут"

    await state.update_data(client_type=client_type)

    details = await db.get_setting("prepayment_details")

    await message.answer(
        f"💳 Для подтверждения записи\n"
        f"необходима предоплата {prepayment} руб\n\n"
        f"📋 Реквизиты для оплаты:\n{details}\n\n"
        f"⚠️ Без предоплаты запись невозможна\n"
        f"⏱ Длительность: {duration}\n\n"
        f"После оплаты выберите дату 👇"
    )

    # Показываем даты в зависимости от типа
    if client_type == "primary":
        dates_with_slots = []
        all_dates = await db.get_all_dates_admin()
        for d in all_dates:
            slots = await db.get_free_slots_for_primary(d)
            if slots:
                dates_with_slots.append(d)
        dates = dates_with_slots
    else:
        dates = await db.get_available_dates()

    if not dates:
        await message.answer(
            "😔 На данный момент нет доступных дат\n\n"
            "Свяжитесь с нами или загляните позже",
            reply_markup=client_kb.main_menu()
        )
        await state.clear()
        return

    await state.set_state(BookingStates.choosing_date)
    await message.answer(
        "📅 Выберите удобную дату:",
        reply_markup=client_kb.dates_keyboard(dates)
    )


@router.message(
    BookingStates.choosing_type,
    F.text == "🚫 Отменить запись"
)
async def cancel_type_choice(
    message: Message,
    state: FSMContext
):
    await state.clear()
    await message.answer(
        "❌ Запись отменена",
        reply_markup=client_kb.main_menu()
    )


# ==================== ВЫБОР ДАТЫ ====================

@router.callback_query(
    BookingStates.choosing_date,
    F.data.startswith("date_")
)
async def choose_date(
    callback: CallbackQuery,
    state: FSMContext
):
    date = callback.data.split("_", 1)[1]
    await state.update_data(chosen_date=date)

    data = await state.get_data()
    client_type = data.get("client_type", "primary")

    if client_type == "primary":
        times = await db.get_free_slots_for_primary(date)
    else:
        times = await db.get_free_slots_for_repeated(date)

    if not times:
        await callback.message.edit_text(
            "😔 На эту дату нет подходящего времени\n"
            "Выберите другую дату:",
            reply_markup=client_kb.dates_keyboard(
                await db.get_available_dates()
            )
        )
        return

    await state.set_state(BookingStates.choosing_time)
    await callback.message.edit_text(
        "🕐 Выберите удобное время:",
        reply_markup=client_kb.times_keyboard(times, date)
    )


@router.callback_query(F.data == "back_to_dates")
async def back_to_dates(
    callback: CallbackQuery,
    state: FSMContext
):
    data = await state.get_data()
    client_type = data.get("client_type", "primary")

    if client_type == "primary":
        all_dates = await db.get_all_dates_admin()
        dates = []
        for d in all_dates:
            slots = await db.get_free_slots_for_primary(d)
            if slots:
                dates.append(d)
    else:
        dates = await db.get_available_dates()

    await state.set_state(BookingStates.choosing_date)
    await callback.message.edit_text(
        "📅 Выберите удобную дату:",
        reply_markup=client_kb.dates_keyboard(dates)
    )


# ==================== ВЫБОР ВРЕМЕНИ ====================

@router.callback_query(
    BookingStates.choosing_time,
    F.data.startswith("time_")
)
async def choose_time(
    callback: CallbackQuery,
    state: FSMContext
):
    parts = callback.data.split("_")
    date = parts[1]
    time = parts[2]

    await state.update_data(chosen_time=time)
    await state.set_state(BookingStates.entering_name)

    d = date.split("-")
    pretty_date = f"{d[2]}.{d[1]}.{d[0]}"

    await callback.message.edit_text(
        f"✅ Выбрано: {pretty_date} в {time}\n\n"
        "📝 Заполните анкету\n\n"
        "Введите ваше имя и фамилию:"
    )


# ==================== АНКЕТА ====================

@router.message(BookingStates.entering_name)
async def enter_name(message: Message, state: FSMContext):
    if message.text == "🚫 Отменить запись":
        await cancel_booking_handler(message, state)
        return
    await state.update_data(client_name=message.text)
    await state.set_state(BookingStates.entering_age)
    await message.answer(
        f"👤 Имя: {message.text}\n\n"
        "Введите ваш возраст:",
        reply_markup=client_kb.cancel_keyboard()
    )


@router.message(BookingStates.entering_age)
async def enter_age(message: Message, state: FSMContext):
    if message.text == "🚫 Отменить запись":
        await cancel_booking_handler(message, state)
        return
    if not message.text.isdigit():
        await message.answer(
            "❌ Введите возраст цифрами\nНапример: 35"
        )
        return
    age = int(message.text)
    if age < 1 or age > 120:
        await message.answer(
            "❌ Введите корректный возраст"
        )
        return
    await state.update_data(client_age=age)
    await state.set_state(BookingStates.entering_phone)
    await message.answer(
        f"🎂 Возраст: {age}\n\n"
        "Введите ваш номер телефона:\n"
        "Например: +7 928 123 45 67",
        reply_markup=client_kb.cancel_keyboard()
    )


@router.message(BookingStates.entering_phone)
async def enter_phone(message: Message, state: FSMContext):
    if message.text == "🚫 Отменить запись":
        await cancel_booking_handler(message, state)
        return
    phone = message.text.strip()
    digits = ''.join(filter(str.isdigit, phone))
    if len(digits) < 10:
        await message.answer(
            "❌ Введите корректный номер телефона\n"
            "Например: +7 928 123 45 67"
        )
        return
    await state.update_data(client_phone=phone)
    await state.set_state(BookingStates.entering_diseases)
    await message.answer(
        f"📱 Телефон: {phone}\n\n"
        "Есть ли у вас хронические заболевания?",
        reply_markup=client_kb.yes_no_keyboard()
    )


@router.message(BookingStates.entering_diseases)
async def enter_diseases(
    message: Message,
    state: FSMContext
):
    if message.text == "🚫 Отменить запись":
        await cancel_booking_handler(message, state)
        return
    if message.text not in ["✅ Да", "❌ Нет"]:
        await message.answer(
            "Нажмите кнопку ✅ Да или ❌ Нет",
            reply_markup=client_kb.yes_no_keyboard()
        )
        return
    has_diseases = (
        "Да" if message.text == "✅ Да" else "Нет"
    )
    await state.update_data(has_diseases=has_diseases)
    await state.set_state(BookingStates.entering_complaint)
    await message.answer(
        f"🏥 Хронические заболевания: {has_diseases}\n\n"
        "Опишите цель визита или жалобу:\n"
        "(например: усталость, боли в суставах)",
        reply_markup=client_kb.cancel_keyboard()
    )


@router.message(BookingStates.entering_complaint)
async def enter_complaint(
    message: Message,
    state: FSMContext
):
    if message.text == "🚫 Отменить запись":
        await cancel_booking_handler(message, state)
        return
    await state.update_data(complaint=message.text)
    await state.set_state(BookingStates.confirming)

    data = await state.get_data()
    date = data['chosen_date']
    d = date.split("-")
    pretty_date = f"{d[2]}.{d[1]}.{d[0]}"

    client_type = data.get("client_type", "primary")
    if client_type == "primary":
        type_text = "🆕 Первичка (40 мин)"
        prepayment = await db.get_setting(
            "prepayment_primary"
        )
    else:
        type_text = "🔄 Повторник (20 мин)"
        prepayment = await db.get_setting(
            "prepayment_repeated"
        )

    await message.answer(
        "📋 Проверьте вашу запись:\n\n"
        f"📅 Дата: {pretty_date}\n"
        f"🕐 Время: {data['chosen_time']}\n"
        f"👤 Тип: {type_text}\n"
        f"👤 Имя: {data['client_name']}\n"
        f"🎂 Возраст: {data['client_age']}\n"
        f"📱 Телефон: {data['client_phone']}\n"
        f"🏥 Хрон. заболевания: {data['has_diseases']}\n"
        f"💬 Жалоба: {message.text}\n\n"
        f"💳 Предоплата: {prepayment} руб\n\n"
        "Подтвердить запись?",
        reply_markup=client_kb.confirm_keyboard()
    )


# ==================== ПОДТВЕРЖДЕНИЕ ====================

@router.callback_query(
    BookingStates.confirming,
    F.data == "confirm_booking"
)
async def confirm_booking(
    callback: CallbackQuery,
    state: FSMContext
):
    data = await state.get_data()
    date = data['chosen_date']
    time = data['chosen_time']
    client_type = data.get("client_type", "primary")

    d = date.split("-")
    pretty_date = f"{d[2]}.{d[1]}.{d[0]}"

    if client_type == "primary":
        type_text = "🆕 Первичка (40 мин)"
        prepayment = await db.get_setting(
            "prepayment_primary"
        )
    else:
        type_text = "🔄 Повторник (20 мин)"
        prepayment = await db.get_setting(
            "prepayment_repeated"
        )

    details = await db.get_setting("prepayment_details")

    # Сохраняем запись в базу
    booking_id = await db.add_booking(
        user_telegram_id=callback.from_user.id,
        client_name=data['client_name'],
        client_age=data['client_age'],
        client_phone=data['client_phone'],
        has_diseases=data['has_diseases'],
        complaint=data['complaint'],
        client_type=client_type,
        date=date,
        time=time
    )

    await state.clear()

    # Сообщение клиенту
    await callback.message.edit_text(
        "✅ Заявка отправлена!\n\n"
        f"📅 Дата: {pretty_date}\n"
        f"🕐 Время: {time}\n"
        f"👤 Тип: {type_text}\n\n"
        f"💳 Пожалуйста оплатите предоплату "
        f"{prepayment} рублей:\n\n"
        f"{details}\n\n"
        "⏳ После оплаты ожидайте подтверждения\n"
        "Мы проверим оплату и одобрим запись 🌿"
    )

    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=client_kb.main_menu()
    )

    # Уведомление админу с кнопками одобрения
    try:
        await callback.bot.send_message(
            ADMIN_ID,
            f"🆕 Новая заявка на запись!\n\n"
            f"🆔 ID записи: {booking_id}\n"
            f"📅 Дата: {pretty_date}\n"
            f"🕐 Время: {time}\n"
            f"👤 Тип: {type_text}\n"
            f"👤 Имя: {data['client_name']}\n"
            f"🎂 Возраст: {data['client_age']}\n"
            f"📱 Телефон: {data['client_phone']}\n"
            f"🏥 Хрон. заболевания: {data['has_diseases']}\n"
            f"💬 Жалоба: {data['complaint']}\n\n"
            f"💳 Предоплата: {prepayment} руб\n\n"
            "Проверьте оплату и одобрите или отклоните:",
            reply_markup=admin_kb.approve_booking_keyboard(
                booking_id
            )
        )
    except Exception:
        pass


# ==================== ОДОБРЕНИЕ ЗАПИСИ ====================

@router.callback_query(F.data.startswith("approve_"))
async def approve_booking(
    callback: CallbackQuery
):
    booking_id = int(callback.data.split("_")[1])
    booking = await db.approve_booking(booking_id)

    if not booking:
        await callback.answer("❌ Запись не найдена")
        return

    (b_id, user_id, name, age, phone,
     diseases, complaint, client_type,
     date, time, status, reminder, created) = booking

    d = date.split("-")
    pretty_date = f"{d[2]}.{d[1]}.{d[0]}"

    address = await db.get_setting("address")

    # Убираем кнопки у сообщения
    await callback.message.edit_reply_markup(
        reply_markup=None
    )
    await callback.message.answer(
        f"✅ Запись #{booking_id} одобрена!"
    )

    # Уведомляем клиента
    try:
        type_text = (
            "🆕 Первичка (40 мин)"
            if client_type == "primary"
            else "🔄 Повторник (20 мин)"
        )
        await callback.bot.send_message(
            user_id,
            f"✅ Ваша запись подтверждена!\n\n"
            f"📅 Дата: {pretty_date}\n"
            f"🕐 Время: {time}\n"
            f"👤 Тип: {type_text}\n\n"
            f"📍 Адрес:\n{address}\n\n"
            "🔔 Мы напомним вам за день до визита\n\n"
            "Ждём вас! 🌿"
        )
    except Exception:
        pass


# ==================== ОТКЛОНЕНИЕ ЗАПИСИ ====================

@router.callback_query(F.data.startswith("reject_"))
async def reject_booking(
    callback: CallbackQuery
):
    booking_id = int(callback.data.split("_")[1])
    booking = await db.reject_booking(booking_id)

    if not booking:
        await callback.answer("❌ Запись не найдена")
        return

    (b_id, user_id, name, age, phone,
     diseases, complaint, client_type,
     date, time, status, reminder, created) = booking

    # Убираем кнопки
    await callback.message.edit_reply_markup(
        reply_markup=None
    )
    await callback.message.answer(
        f"❌ Запись #{booking_id} отклонена"
    )

    # Уведомляем клиента
    try:
        contacts = await db.get_setting("contacts")
        await callback.bot.send_message(
            user_id,
            "❌ К сожалению ваша запись отклонена\n\n"
            "Возможные причины:\n"
            "• Оплата не поступила\n"
            "• Технические проблемы\n\n"
            f"Свяжитесь с нами для уточнения:\n"
            f"{contacts}",
            reply_markup=client_kb.main_menu()
        )
    except Exception:
        pass


# ==================== ОТМЕНА ====================

@router.callback_query(F.data == "cancel_booking")
async def cancel_booking_callback(
    callback: CallbackQuery,
    state: FSMContext
):
    await state.clear()
    await callback.message.edit_text("❌ Запись отменена")
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=client_kb.main_menu()
    )


async def cancel_booking_handler(
    message: Message,
    state: FSMContext
):
    await state.clear()
    await message.answer(
        "❌ Запись отменена",
        reply_markup=client_kb.main_menu()
    )