from aiogram import Router, F
from aiogram.types import CallbackQuery
from middlewares import (
    check_subscription,
    subscription_keyboard
)
from keyboards import client_kb
from config import ADMIN_ID

router = Router()


@router.callback_query(
    F.data == "check_subscription"
)
async def check_sub_callback(
    callback: CallbackQuery
):
    """Проверяем подписку когда нажали кнопку"""
    user_id = callback.from_user.id
    bot = callback.bot

    is_subscribed = await check_subscription(
        bot, user_id
    )

    if is_subscribed:
        await callback.message.delete()
        await callback.message.answer(
            "✅ Отлично! Вы подписаны!\n\n"
            "Добро пожаловать в TIENS Черкесск! 🌿",
            reply_markup=client_kb.main_menu()
        )
    else:
        await callback.answer(
            "❌ Вы ещё не подписались на канал!",
            show_alert=True
        )
        await callback.message.edit_reply_markup(
            reply_markup=subscription_keyboard()
        )