from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import database as db


async def send_reminders(bot):
    """Отправляем напоминания за день до визита"""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    reminders = await db.get_reminders_to_send(tomorrow)

    for booking_id, user_id, name, time in reminders:
        tomorrow_pretty = (
            datetime.now() + timedelta(days=1)
        ).strftime("%d.%m.%Y")

        address = await db.get_setting("address")

        try:
            await bot.send_message(
                user_id,
                f"🔔 Напоминание!\n\n"
                f"Здравствуйте, {name}!\n\n"
                f"Завтра {tomorrow_pretty} в {time} "
                f"у вас запись на тестирование\n\n"
                f"📍 Адрес:\n{address}\n\n"
                f"Если не сможете прийти — "
                f"пожалуйста свяжитесь с нами заранее"
            )
            await db.mark_reminder_sent(booking_id)
        except Exception:
            pass


def setup_scheduler(bot):
    """Запускаем планировщик"""
    scheduler = AsyncIOScheduler()

    # Каждый день в 10:00 отправляем напоминания
    scheduler.add_job(
        send_reminders,
        trigger="cron",
        hour=10,
        minute=0,
        args=[bot]
    )

    scheduler.start()
    return scheduler