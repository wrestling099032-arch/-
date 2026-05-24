import aiosqlite
from datetime import datetime, timedelta

DB_NAME = "tiens_bot.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                full_name TEXT,
                joined_at TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                time TEXT,
                status TEXT DEFAULT 'free',
                UNIQUE(date, time)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_telegram_id INTEGER,
                client_name TEXT,
                client_age INTEGER,
                client_phone TEXT,
                has_diseases TEXT,
                complaint TEXT,
                client_type TEXT,
                date TEXT,
                time TEXT,
                status TEXT DEFAULT 'pending',
                reminder_sent INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                emoji TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                name TEXT,
                description TEXT,
                price TEXT,
                photo_id TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                answer TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS social_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                url TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                photo_id TEXT,
                added_at TEXT
            )
        """)

        await db.commit()
        await set_default_settings(db)
        await set_default_faq(db)
        await set_default_socials(db)


async def set_default_settings(db):
    defaults = {
        "address": "г. Черкесск — укажите адрес в админ панели",
        "contacts": "Укажите контакты в админ панели",
        "about_testing": (
            "🔬 Тестирование организма на клеточном уровне\n\n"
            "Это современный метод диагностики который позволяет "
            "выявить проблемы на раннем этапе.\n\n"
            "✅ Что мы проверяем:\n"
            "• Состояние внутренних органов\n"
            "• Уровень витаминов и минералов\n"
            "• Состояние иммунной системы\n"
            "• Энергетический баланс организма\n\n"
            "⏱ Первичка: 40 минут\n"
            "⏱ Повторник: 20 минут\n"
            "📍 Город Черкесск"
        ),
        "prepayment_primary": "1500",
        "prepayment_repeated": "500",
        "prepayment_details": "Укажите реквизиты для оплаты в админ панели"
    }
    for key, value in defaults.items():
        await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))
    await db.commit()


async def set_default_faq(db):
    faqs = [
        ("Что такое тестирование на клеточном уровне?", 
         "Это современный метод диагностики организма который позволяет выявить проблемы на раннем этапе и подобрать подходящие решения для вашего здоровья."),
        ("Больно ли это?", 
         "Нет — тестирование абсолютно безболезненно и не требует никаких уколов или анализов крови."),
        ("Сколько длится тестирование?", 
         "Первичное тестирование — 40 минут.\nПовторное тестирование — 20 минут."),
        ("Нужна ли подготовка перед тестированием?", 
         "Желательно прийти натощак или через 2 часа после еды. Не принимайте лекарства за 1 час до процедуры."),
        ("Сколько стоит предоплата?", 
         "Первичное тестирование — предоплата 1500 рублей.\nПовторное тестирование — предоплата 500 рублей.\nБез предоплаты запись невозможна."),
    ]
    for question, answer in faqs:
        await db.execute("INSERT OR IGNORE INTO faq (question, answer) VALUES (?, ?)", (question, answer))
    await db.commit()


async def set_default_socials(db):
    socials = [
        ("Telegram", "Укажите ссылку в админ панели"),
        ("WhatsApp", "Укажите ссылку в админ панели"),
        ("BIP", "Укажите ссылку в админ панели"),
    ]
    for name, url in socials:
        await db.execute("INSERT OR IGNORE INTO social_links (name, url) VALUES (?, ?)", (name, url))
    await db.commit()


# ==================== ПОЛЬЗОВАТЕЛИ ====================
async def add_user(telegram_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (telegram_id, username, full_name, joined_at)
            VALUES (?, ?, ?, ?)
        """, (telegram_id, username, full_name, datetime.now().strftime("%Y-%m-%d %H:%M")))
        await db.commit()


async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT telegram_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def get_users_count():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0]


# ==================== РАСПИСАНИЕ ====================
async def add_schedule_slots(date: str, time_start: str, time_end: str, lunch_start: str = None, lunch_end: str = None):
    """Слоты по 20 минут. Первичка занимает 2 слота, Повторник занимает 1 слот"""
    start = datetime.strptime(time_start, "%H:%M")
    end = datetime.strptime(time_end, "%H:%M")
    lunch_s = None
    lunch_e = None
    if lunch_start and lunch_end:
        lunch_s = datetime.strptime(lunch_start, "%H:%M")
        lunch_e = datetime.strptime(lunch_end, "%H:%M")

    slots_added = 0
    current = start

    async with aiosqlite.connect(DB_NAME) as db:
        while current < end:
            if lunch_s and lunch_e:
                if lunch_s <= current < lunch_e:
                    time_str = current.strftime("%H:%M")
                    try:
                        await db.execute("INSERT OR IGNORE INTO schedule (date, time, status) VALUES (?, ?, 'lunch')", (date, time_str))
                    except Exception:
                        pass
                    current += timedelta(minutes=20)
                    continue

            time_str = current.strftime("%H:%M")
            try:
                await db.execute("INSERT OR IGNORE INTO schedule (date, time, status) VALUES (?, ?, 'free')", (date, time_str))
                slots_added += 1
            except Exception:
                pass
            current += timedelta(minutes=20)
        await db.commit()

    return slots_added


async def get_available_dates():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT DISTINCT date FROM schedule
            WHERE status = 'free' AND date >= date('now')
            ORDER BY date
        """) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def get_slots_by_date(date: str):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT time, status FROM schedule WHERE date = ? ORDER BY time", (date,)) as cursor:
            return await cursor.fetchall()


async def get_free_slots_for_primary(date: str):
    """Для первички нужно 2 подряд свободных слота. Возвращаем только первый слот из пары"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT time FROM schedule WHERE date = ? AND status = 'free' ORDER BY time", (date,)) as cursor:
            rows = await cursor.fetchall()
            times = [row[0] for row in rows]
            available = []
            for i in range(len(times) - 1):
                t1 = datetime.strptime(times[i], "%H:%M")
                t2 = datetime.strptime(times[i + 1], "%H:%M")
                if (t2 - t1).seconds == 20 * 60:
                    available.append(times[i])
            return available


async def get_free_slots_for_repeated(date: str):
    """Для повторника нужен 1 свободный слот"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT time FROM schedule WHERE date = ? AND status = 'free' ORDER BY time", (date,)) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def update_slot_status(date: str, time: str, status: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE schedule SET status = ? WHERE date = ? AND time = ?", (status, date, time))
        await db.commit()


async def block_primary_slots(date: str, time: str):
    """Блокируем 2 слота для первички"""
    t1 = datetime.strptime(time, "%H:%M")
    t2 = t1 + timedelta(minutes=20)
    t2_str = t2.strftime("%H:%M")
    await update_slot_status(date, time, "booked")
    await update_slot_status(date, t2_str, "booked")


async def free_primary_slots(date: str, time: str):
    """Освобождаем 2 слота первички"""
    t1 = datetime.strptime(time, "%H:%M")
    t2 = t1 + timedelta(minutes=20)
    t2_str = t2.strftime("%H:%M")
    await update_slot_status(date, time, "free")
    await update_slot_status(date, t2_str, "free")


async def delete_date(date: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM schedule WHERE date = ?", (date,))
        await db.commit()


async def get_all_dates_admin():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT DISTINCT date FROM schedule ORDER BY date") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


# ==================== ЗАПИСИ ====================
async def add_booking(user_telegram_id: int, client_name: str, client_age: int, client_phone: str, has_diseases: str, complaint: str, client_type: str, date: str, time: str):
    """Создаём запись со статусом pending. Слоты блокируем сразу чтобы никто не занял"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO bookings (user_telegram_id, client_name, client_age,
                                  client_phone, has_diseases, complaint,
                                  client_type, date, time, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (user_telegram_id, client_name, client_age,
              client_phone, has_diseases, complaint,
              client_type, date, time,
              datetime.now().strftime("%Y-%m-%d %H:%M")))
        await db.commit()

    if client_type == "primary":
        await block_primary_slots(date, time)
    else:
        await update_slot_status(date, time, "booked")

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT id FROM bookings WHERE user_telegram_id = ? AND date = ? AND time = ? ORDER BY id DESC LIMIT 1
        """, (user_telegram_id, date, time)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def approve_booking(booking_id: int):
    """Одобряем запись"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE bookings SET status = 'approved' WHERE id = ?", (booking_id,))
        await db.commit()
    return await get_booking_by_id(booking_id)


async def reject_booking(booking_id: int):
    """Отклоняем запись и освобождаем слоты"""
    booking = await get_booking_by_id(booking_id)
    if not booking:
        return None
    (b_id, user_id, name, age, phone, diseases, complaint, client_type, date, time, status, reminder, created) = booking

    if client_type == "primary":
        await free_primary_slots(date, time)
    else:
        await update_slot_status(date, time, "free")

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE bookings SET status = 'rejected' WHERE id = ?", (booking_id,))
        await db.commit()
    return booking


async def get_bookings_by_date(date: str, exclude_rejected: bool = True):
    async with aiosqlite.connect(DB_NAME) as db:
        if exclude_rejected:
            async with db.execute("""
                SELECT id, client_name, client_age,
                       client_phone, has_diseases,
                       complaint, client_type,
                       time, status
                FROM bookings
                WHERE date = ?
                AND status != 'rejected'
                ORDER BY time
            """, (date,)) as cursor:
                return await cursor.fetchall()
        else:
            async with db.execute("""
                SELECT id, client_name, client_age,
                       client_phone, has_diseases,
                       complaint, client_type,
                       time, status
                FROM bookings
                WHERE date = ?
                ORDER BY time
            """, (date,)) as cursor:
                return await cursor.fetchall()


async def get_booking_by_id(booking_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)) as cursor:
            return await cursor.fetchone()


async def cancel_booking(booking_id: int):
    """Отмена записи админом"""
    booking = await get_booking_by_id(booking_id)
    if not booking:
        return None
    (b_id, user_id, name, age, phone, diseases, complaint, client_type, date, time, status, reminder, created) = booking

    if client_type == "primary":
        await free_primary_slots(date, time)
    else:
        await update_slot_status(date, time, "free")

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        await db.commit()
    return user_id


async def get_bookings_count():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM bookings WHERE status = 'approved'") as cursor:
            row = await cursor.fetchone()
            return row[0]


async def get_reminders_to_send(tomorrow_date: str):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT id, user_telegram_id, client_name, time
            FROM bookings
            WHERE date = ? AND reminder_sent = 0 AND status = 'approved'
        """, (tomorrow_date,)) as cursor:
            return await cursor.fetchall()


async def mark_reminder_sent(booking_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE bookings SET reminder_sent = 1 WHERE id = ?", (booking_id,))
        await db.commit()


# ==================== ПРОДУКЦИЯ ====================
async def add_category(name: str, emoji: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO categories (name, emoji) VALUES (?, ?)", (name, emoji))
        await db.commit()


async def get_categories():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id, name, emoji FROM categories ORDER BY id") as cursor:
            return await cursor.fetchall()


async def add_product(category_id: int, name: str, description: str, price: str, photo_id: str = None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO products (category_id, name, description, price, photo_id)
            VALUES (?, ?, ?, ?, ?)
        """, (category_id, name, description, price, photo_id))
        await db.commit()


async def get_products_by_category(category_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT id, name, description, price, photo_id FROM products WHERE category_id = ?
        """, (category_id,)) as cursor:
            return await cursor.fetchall()


async def get_product_by_id(product_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT id, name, description, price, photo_id, category_id FROM products WHERE id = ?
        """, (product_id,)) as cursor:
            return await cursor.fetchone()


async def delete_product(product_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.commit()


async def delete_category(category_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM products WHERE category_id = ?", (category_id,))
        await db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        await db.commit()


async def edit_product(product_id: int, name: str, description: str, price: str, photo_id: str = None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE products SET name=?, description=?, price=?, photo_id=? WHERE id = ?
        """, (name, description, price, photo_id, product_id))
        await db.commit()


# ==================== СЕРТИФИКАТЫ ====================
async def add_certificate(title: str, photo_id: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO certificates (title, photo_id, added_at)
            VALUES (?, ?, ?)
        """, (title, photo_id, datetime.now().strftime("%Y-%m-%d %H:%M")))
        await db.commit()


async def get_certificates():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id, title, photo_id FROM certificates ORDER BY id") as cursor:
            return await cursor.fetchall()


async def delete_certificate(cert_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM certificates WHERE id = ?", (cert_id,))
        await db.commit()


# ==================== НАСТРОЙКИ ====================
async def get_setting(key: str):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def update_setting(key: str, value: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        await db.commit()


# ==================== СОЦИАЛЬНЫЕ СЕТИ ====================
async def get_social_links():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id, name, url FROM social_links ORDER BY id") as cursor:
            return await cursor.fetchall()


async def update_social_link(name: str, url: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE social_links SET url = ? WHERE name = ?", (url, name))
        await db.commit()


# ==================== FAQ ====================
async def get_faq():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id, question, answer FROM faq") as cursor:
            return await cursor.fetchall()


async def add_faq(question: str, answer: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO faq (question, answer) VALUES (?, ?)", (question, answer))
        await db.commit()


async def delete_faq(faq_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM faq WHERE id = ?", (faq_id,))
        await db.commit()


# ==================== РУЧНАЯ ЗАПИСЬ ====================
async def add_manual_booking(
    client_name: str,
    client_age: int,
    client_phone: str,
    has_diseases: str,
    complaint: str,
    client_type: str,
    date: str,
    time: str
):
    """Добавляем запись вручную без telegram ID"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO bookings
            (user_telegram_id, client_name,
             client_age, client_phone,
             has_diseases, complaint,
             client_type, date, time,
             status, created_at)
            VALUES (0, ?, ?, ?, ?, ?, ?, ?, ?,
                    'approved', ?)
        """, (
            client_name, client_age,
            client_phone, has_diseases,
            complaint, client_type,
            date, time,
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ))
        await db.commit()

    if client_type == "primary":
        await block_primary_slots(date, time)
    else:
        await update_slot_status(date, time, "booked")