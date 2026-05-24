from aiogram import BaseMiddleware
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from typing import Callable, Dict, Any, Awaitable
from config import CHANNEL_USERNAME, CHANNEL_ID, ADMIN_ID


async def check_subscription(
    bot,
    user_id: int
) -> bool:
    """Проверяем подписан ли пользователь на канал"""
    try:
        member = await bot.get_chat_member(
            CHANNEL_ID, user_id
        )
        return member.status in [
            "member",
            "administrator",
            "creator"
        ]
    except Exception:
        return False


def subscription_keyboard():
    """Кнопки для подписки"""
    buttons = [
        [
            InlineKeyboardButton(
                text="📢 Подписаться на канал",
                url=f"https://t.me/{CHANNEL_USERNAME}"
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Я подписался",
                callback_data="check_subscription"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


class SubscriptionMiddleware(BaseMiddleware):
    """
    Middleware проверяет подписку
    перед каждым сообщением
    """

    async def __call__(
        self,
        handler: Callable[
            [Message, Dict[str, Any]],
            Awaitable[Any]
        ],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:

        # Пропускаем проверку для админа
        if event.from_user.id == ADMIN_ID:
            return await handler(event, data)

        # Пропускаем команду /start
        if (
            hasattr(event, 'text') and
            event.text and
            event.text.startswith('/start')
        ):
            return await handler(event, data)

        bot = data['bot']
        user_id = event.from_user.id

        # Проверяем подписку
        is_subscribed = await check_subscription(
            bot, user_id
        )

        if not is_subscribed:
            await event.answer(
                "👋 Для использования бота\n"
                "необходимо подписаться на наш канал!\n\n"
                "📢 Подпишитесь и нажмите "
                "✅ Я подписался",
                reply_markup=subscription_keyboard()
            )
            return

        return await handler(event, data)