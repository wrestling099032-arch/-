# ============================================================
# Teberda & Dombay Guide Bot 7.0 FULL (с меню выбора VIP)
# aiogram 2.25.1
# ============================================================
import os
import logging
import json
import datetime
import asyncio
import aiohttp
import pytz
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# ================== BASE DIR ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def p(filename: str) -> str:
    return os.path.join(BASE_DIR, filename)

def norm(text: str) -> str:
    if text is None:
        return ""
    return " ".join(text.replace("\u00a0", " ").strip().split())

# ================= НАСТРОЙКИ =================
API_TOKEN = "8407548042:AAE5MOQfP9RvVbUzwpB9Xg-sNT1dRvKRR_g"
ADMIN_ID = 988124332

SITE_URL = "https://teberda-dombay-gid.ru/"
CHANNEL_URL = "https://t.me/TeberdaDombayNews"
CHANNEL_ID = "@TeberdaDombayNews"
CHAT_URL = "https://t.me/+cy0Vxh-BrbpiNzli"
GUIDE_APP_URL = "https://wrestling099032-arch.github.io/guide-bot/"
MUSIC_URL = "https://t.me/tipopesen"

# ===== AI =====
GROQ_API_KEY = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCIsImtpZCI6IjFrYnhacFJNQGJSI0tSbE1xS1lqIn0.eyJ1c2VyIjoic2QyMDY4MDAiLCJ0eXBlIjoiYXBpX2tleSIsImFwaV9rZXlfaWQiOiJjZDA1ZTg0OC1kNmQ5LTQ5ZjktYTVjMy04MjA2ZDk5YTE5ZmEiLCJpYXQiOjE3NzI1NTQ3OTR9.mlPywz7YKiHjg6LONsxQ1QlWmwwQfNjq1nABnkm_pYUjWig-Yjnm4v8QfXjpsdjqI7Bc3IFFKGBX7dndTiG1lsrLr-uduMHa41oYoUU7LPX7MYcu4JVdsKlodrX6-Tlo7ISK5uPwk559R7DiTm4YbRi6X-JKiiekhTiuWgacQilsMX89-zKiDkkjRVFt99a3nNx_DrXxtg4Suk1IDjwVYe7AvddxjxyzdXGv0uLDBF7Cru1E3S34PMw9uqR62R43HGppequawy6eh7Rr6uKFjWzPMOi7iyZAsn5UIUOT32BfsqPmbf-iudUIOuqLYCnxp-08sXCV7MPOuIlStnnIMXoB-3gafgfisw6bp08WsYvWQzj0w1SpXn_ynfCE2t42G33hQAs8vBq1PxtTIh9sRvm9h3CDZX3D9oEE31_kIWTqVhXeZGplFvfvXb56RIluK3dQzWDM62cLb8HSrZ0kIoCjcIz4ux1Ho4rJd_OGMhG2nnblHYMzgNT-E6Wa49jS"
GROQ_API_URL = "https://agent.timeweb.cloud/api/v1/cloud-ai/agents/355ee023-b6fe-4edc-a733-4d1ae4e2c9af/v1/chat/completions"
GROQ_MODEL = "gemini/gemini-2.5-flash-lite"
AI_DAILY_LIMIT = 10

AI_SYSTEM_PROMPT = """
Ты — умный туристический гид по Карачаево‑Черкесской Республике (КЧР) и Кавказу.
Особенно подробно знаешь: Теберду и Домбай.

Умеешь:
— советовать куда сходить (места, прогулки, маршруты, смотровые, канатки, водопады, озёра)
— подбирать маршрут по уровню, времени и сезону
— давать список экипировки: что брать, какую обувь и одежду слоями, аптечку
— безопасность в горах: погода, ветер, гроза, туман, лавины зимой, связь, вода
— логистика: как добраться, транспорт, жильё

Стиль: понятно, структурировано, полезно, дружелюбно. Эмодзи умеренно.
"""

# ================= ФАЙЛЫ =================
USERS_FILE = p("users.json")
SUBS_FILE = p("weather_subs.json")
LIMITS_FILE = p("ai_limits.json")
SERVICES_FILE = p("services.json")
SETTINGS_FILE = p("settings.json")

# ================= INIT =================
logging.basicConfig(level=logging.INFO)
PROXY_URL = "http://eWk8kg:mv6xJt@196.18.13.49:8000"
bot = Bot(token=API_TOKEN, proxy=PROXY_URL)
dp = Dispatcher(bot, storage=MemoryStorage())
AI_STATE = {}

# ================= JSON HELPERS =================
def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_json_file(path, default):
    if not os.path.exists(path):
        save_json(path, default)

def add_user(uid: int):
    users = load_json(USERS_FILE, [])
    if uid not in users:
        users.append(uid)
        save_json(USERS_FILE, users)

# ================= SETTINGS =================
def load_settings():
    st = load_json(SETTINGS_FILE, {})
    if not isinstance(st, dict):
        st = {}
    st.setdefault("services_limit", 5)
    st.setdefault("service_ttl_days", 30)
    save_json(SETTINGS_FILE, st)
    return st

def get_services_limit() -> int:
    return int(load_settings().get("services_limit", 5))

def set_services_limit(n: int):
    st = load_settings()
    st["services_limit"] = int(n)
    save_json(SETTINGS_FILE, st)

def get_service_ttl_days() -> int:
    return int(load_settings().get("service_ttl_days", 30))

def set_service_ttl_days(n: int):
    st = load_settings()
    st["service_ttl_days"] = int(n)
    save_json(SETTINGS_FILE, st)

# ================= AI LIMIT =================
def check_limit(uid):
    if uid == ADMIN_ID:
        return True, 999
    limits = load_json(LIMITS_FILE, {})
    today = datetime.date.today().isoformat()
    rec = limits.get(str(uid))
    if not rec or rec.get("date") != today:
        return True, AI_DAILY_LIMIT
    used = int(rec.get("count", 0))
    return used < AI_DAILY_LIMIT, AI_DAILY_LIMIT - used

def use_limit(uid):
    if uid == ADMIN_ID:
        return
    limits = load_json(LIMITS_FILE, {})
    today = datetime.date.today().isoformat()
    rec = limits.get(str(uid))
    if not rec or rec.get("date") != today:
        limits[str(uid)] = {"date": today, "count": 1}
    else:
        rec["count"] = int(rec.get("count", 0)) + 1
        limits[str(uid)] = rec
    save_json(LIMITS_FILE, limits)

# ================= КНОПКИ / МЕНЮ =================
BTN_APP = "📱 Открыть приложение"
BTN_CHANNEL = "📢 Канал"
BTN_CHAT = "💬 Чат"
BTN_SITE = "🌐 Сайт"
BTN_MUSIC = "🎵 Music"
BTN_SOS = "🆘 SOS"
BTN_WEATHER = "⛅ Погода"
BTN_AI = "🤖 AI Гид"
BTN_VIP_SERVICES = "⭐ VIP Услуги"
BTN_ADD_VIP = "➕ Добавить VIP-услугу"
BTN_ADMIN_PANEL = "⚙ Админ-панель"

A_BACK = "🔙 Назад"
A_BROADCAST = "📣 Рассылка"
A_STATS = "📊 Статистика"
A_MANAGE_VIP = "⭐ Управление VIP-услугами"
A_SET_LIMIT = "🔢 Лимит VIP"
A_SET_TTL = "⏳ Срок VIP (дней)"

SKIP_BTN = "⏭ Пропустить"
CANCEL_BTN = "❌ Отмена"

def main_keyboard(uid: int):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton(BTN_APP, web_app=WebAppInfo(url=GUIDE_APP_URL)))
    kb.add(KeyboardButton(BTN_CHANNEL), KeyboardButton(BTN_CHAT))
    kb.add(KeyboardButton(BTN_SITE), KeyboardButton(BTN_MUSIC))
    kb.add(KeyboardButton(BTN_WEATHER), KeyboardButton(BTN_AI))
    kb.add(KeyboardButton(BTN_VIP_SERVICES), KeyboardButton(BTN_ADD_VIP))
    kb.add(KeyboardButton(BTN_SOS))
    if uid == ADMIN_ID:
        kb.add(KeyboardButton(BTN_ADMIN_PANEL))
    return kb

def admin_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton(A_MANAGE_VIP))
    kb.add(KeyboardButton(A_SET_LIMIT), KeyboardButton(A_SET_TTL))
    kb.add(KeyboardButton(A_BROADCAST), KeyboardButton(A_STATS))
    kb.add(KeyboardButton(A_BACK))
    return kb

def skip_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton(SKIP_BTN))
    kb.add(KeyboardButton(CANCEL_BTN))
    return kb

def cancel_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton(CANCEL_BTN))
    return kb

# ============================================================
# ХРАНЕНИЕ VIP УСЛУГ (с фото)
# ============================================================
def normalize_service_item(item):
    if not isinstance(item, dict):
        return None
    if "owner_id" not in item and "id" in item:
        item["owner_id"] = item.get("id")
    try:
        if item.get("owner_id") is not None:
            item["owner_id"] = int(item["owner_id"])
    except:
        item["owner_id"] = None
    if not item.get("created_at"):
        item["created_at"] = datetime.datetime.utcnow().isoformat()
    if "photos" not in item:
        item["photos"] = []
    return item

def services_store():
    store = load_json(SERVICES_FILE, {"pending": [], "approved": []})
    if isinstance(store, list):
        store = {"pending": [], "approved": store}
    if not isinstance(store, dict):
        store = {"pending": [], "approved": []}
    store.setdefault("pending", [])
    store.setdefault("approved", [])
    if isinstance(store["pending"], dict):
        store["pending"] = list(store["pending"].values())
    if isinstance(store["approved"], dict):
        store["approved"] = list(store["approved"].values())
    if not isinstance(store["pending"], list):
        store["pending"] = []
    if not isinstance(store["approved"], list):
        store["approved"] = []
    store["pending"] = [x for x in (normalize_service_item(i) for i in store["pending"]) if x]
    store["approved"] = [x for x in (normalize_service_item(i) for i in store["approved"]) if x]
    save_json(SERVICES_FILE, store)
    return store

def approved_owner_ids(store) -> set:
    ids = set()
    for s in store.get("approved", []):
        if isinstance(s, dict) and s.get("owner_id") is not None:
            ids.add(str(s["owner_id"]))
    return ids

def service_text(s: dict) -> str:
    """Полная информация об услуге"""
    if not isinstance(s, dict):
        return "⚠ Ошибка данных"
    
    lines = []
    lines.append(f"⭐ <b>{s.get('name', 'Без названия')}</b>")
    lines.append(f"📂 Категория: {s.get('category', '—')}")
    
    desc = str(s.get('desc', '')).strip()
    if desc:
        lines.append(f"\n📝 <b>Описание:</b>\n{desc}")
    
    price = str(s.get('price', '')).strip()
    if price:
        lines.append(f"\n💰 <b>Стоимость:</b> {price}")
    
    city = str(s.get('city', '')).strip()
    address = str(s.get('address', '')).strip()
    if city or address:
        loc_parts = []
        if city:
            loc_parts.append(city)
        if address:
            loc_parts.append(address)
        lines.append(f"\n📍 <b>Локация:</b> {', '.join(loc_parts)}")
    
    # Контакты
    contacts = []
    phone = str(s.get('phone', '')).strip()
    tg = str(s.get('telegram', '')).strip()
    wa = str(s.get('whatsapp', '')).strip()
    
    if phone:
        contacts.append(f"📞 {phone}")
    if tg:
        contacts.append(f"✈ {tg}")
    if wa:
        contacts.append(f"📱 {wa}")
    
    if contacts:
        lines.append(f"\n<b>Контакты:</b>\n" + "\n".join(contacts))
    
    return "\n".join(lines)

def service_buttons(s: dict, with_back: bool = True) -> InlineKeyboardMarkup:
    """Кнопки для услуги"""
    if not isinstance(s, dict):
        return InlineKeyboardMarkup()
    
    kb = InlineKeyboardMarkup(row_width=2)
    
    phone = str(s.get("phone", "")).strip()
    tg = str(s.get("telegram", "")).strip()
    wa = str(s.get("whatsapp", "")).strip()
    vk = str(s.get("vk", "")).strip()
    ig = str(s.get("instagram", "")).strip()
    loc = s.get("location")
    
    # ИСПРАВЛЕНО: НЕ создаём кнопку tel:, просто показываем телефон в тексте
    # Telegram не поддерживает tel: ссылки в inline кнопках
    
    if tg:
        username = tg.replace("@", "").strip()
        if username:
            kb.add(InlineKeyboardButton("✈ Telegram", url=f"https://t.me/{username}"))
    
    if wa:
        wa_num = "".join([c for c in wa if c.isdigit()])
        if wa_num:
            kb.add(InlineKeyboardButton("📱 WhatsApp", url=f"https://wa.me/{wa_num}"))
    
    if vk and vk.startswith("http"):
        kb.add(InlineKeyboardButton("🔵 VK", url=vk))
    
    if ig and ig.startswith("http"):
        kb.add(InlineKeyboardButton("📷 Instagram", url=ig))
    
    if isinstance(loc, dict):
        lat = loc.get("lat")
        lon = loc.get("lon")
        if lat is not None and lon is not None:
            try:
                lat = float(lat)
                lon = float(lon)
                kb.add(InlineKeyboardButton("🗺 На карте", url=f"https://maps.google.com/?q={lat},{lon}"))
            except:
                pass
    
    # Кнопка "Назад к списку"
    if with_back:
        kb.add(InlineKeyboardButton("🔙 К списку услуг", callback_data="vip:list"))
    
    return kb

# ============================================================
# START + DEBUG
# ============================================================
@dp.message_handler(commands=["start"], state="*")
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    add_user(message.from_user.id)
    load_settings()
    services_store()
    migrate_weather_subs()
    await message.answer(
        "🏔 Гид по Кавказу и КЧР\nДомбай • Теберда • Архыз\n\nВыберите раздел 👇",
        reply_markup=main_keyboard(message.from_user.id)
    )

@dp.message_handler(commands=["files"])
async def files_debug(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    def size(path):
        try:
            return os.path.getsize(path)
        except:
            return "нет файла"
    await message.answer(
        "📁 Пути файлов:\n\n"
        f"BASE_DIR: {BASE_DIR}\n\n"
        f"USERS: {USERS_FILE} | size={size(USERS_FILE)}\n"
        f"SUBS: {SUBS_FILE} | size={size(SUBS_FILE)}\n"
        f"LIMITS: {LIMITS_FILE} | size={size(LIMITS_FILE)}\n"
        f"SERVICES: {SERVICES_FILE} | size={size(SERVICES_FILE)}\n"
        f"SETTINGS: {SETTINGS_FILE} | size={size(SETTINGS_FILE)}"
    )

@dp.message_handler(commands=["vipdebug"])
async def vipdebug(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    store = services_store()
    debug_text = "⭐ VIP DEBUG\n\n"
    debug_text += f"approved: {len(store.get('approved', []))}\n"
    debug_text += f"pending: {len(store.get('pending', []))}\n\n"
    
    if store.get('approved'):
        debug_text += "Одобренные:\n"
        for idx, s in enumerate(store['approved'], 1):
            debug_text += f"{idx}. {s.get('name', 'N/A')} | photos: {len(s.get('photos', []))}\n"
    
    await message.answer(debug_text)

# ============================================================
# КНОПКИ (всегда работают)
# ============================================================
@dp.message_handler(lambda m: norm(m.text) == BTN_SITE, state="*")
async def site(message: types.Message, state: FSMContext):
    await state.finish()
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Открыть сайт", url=SITE_URL))
    await message.answer("🌐 Официальный сайт:", reply_markup=kb)

@dp.message_handler(lambda m: norm(m.text) == BTN_MUSIC, state="*")
async def music(message: types.Message, state: FSMContext):
    await state.finish()
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Перейти", url=MUSIC_URL))
    await message.answer("🎵 Music:", reply_markup=kb)

@dp.message_handler(lambda m: norm(m.text) == BTN_CHANNEL, state="*")
async def channel(message: types.Message, state: FSMContext):
    await state.finish()
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Перейти", url=CHANNEL_URL))
    await message.answer("📢 Новости КЧР:", reply_markup=kb)

@dp.message_handler(lambda m: norm(m.text) == BTN_CHAT, state="*")
async def chat(message: types.Message, state: FSMContext):
    await state.finish()
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Войти в чат", url=CHAT_URL))
    await message.answer("💬 Чат туристов:", reply_markup=kb)

@dp.message_handler(lambda m: norm(m.text) == BTN_SOS, state="*")
async def sos(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "🆘 Экстренные службы:\n\n"
        "112 — единый\n"
        "103 — скорая\n"
        "102 — полиция\n"
        "101 — пожарные\n"
        "88782200112 — МЧС"
    )

# ============================================================
# ПОГОДА (КЧР)
# ============================================================
CITY_MAP = {
    "dombay": {"name": "Домбай", "lat": 43.29, "lon": 41.63},
    "teberda": {"name": "Теберда", "lat": 43.45, "lon": 41.74},
    "arkhyz": {"name": "Архыз", "lat": 43.56, "lon": 41.28},
    "cherkessk": {"name": "Черкесск", "lat": 44.22, "lon": 42.06},
    "karachaevsk": {"name": "Карачаевск", "lat": 43.77, "lon": 41.91},
}

WEATHER_CODE = {
    0: "Ясно", 1: "Преимущественно ясно", 2: "Переменная облачность", 3: "Пасмурно",
    45: "Туман", 48: "Туман (изморозь)",
    61: "Дождь слабый", 63: "Дождь", 65: "Дождь сильный",
    71: "Снег слабый", 73: "Снег", 75: "Снег сильный",
    80: "Ливни", 81: "Ливни", 82: "Ливни сильные",
    95: "Гроза",
}

def migrate_weather_subs():
    subs = load_json(SUBS_FILE, {})
    if isinstance(subs, list):
        subs = {str(uid): "dombay" for uid in subs}
        save_json(SUBS_FILE, subs)
    if not isinstance(subs, dict):
        subs = {}
        save_json(SUBS_FILE, subs)
    return subs

async def get_weather(city_code: str) -> str:
    city = CITY_MAP[city_code]
    lat, lon = city["lat"], city["lon"]
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current_weather=true"
        "&hourly=apparent_temperature,relativehumidity_2m,precipitation,visibility,windgusts_10m"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max"
        "&timezone=Europe%2FMoscow"
    )
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as s:
            async with s.get(url) as r:
                data = await r.json()
                cw = data.get("current_weather", {})
                hourly = data.get("hourly", {})
                daily = data.get("daily", {})

                t = cw.get("temperature")
                wind = cw.get("windspeed")
                wcode = cw.get("weathercode")
                ctime = cw.get("time")
                desc = WEATHER_CODE.get(wcode, f"Код погоды: {wcode}")

                idx = None
                times = hourly.get("time", [])
                if ctime in times:
                    idx = times.index(ctime)

                def hget(key):
                    arr = hourly.get(key, [])
                    if idx is None or idx >= len(arr):
                        return None
                    return arr[idx]

                feels = hget("apparent_temperature")
                hum = hget("relativehumidity_2m")
                precip_now = hget("precipitation")
                vis = hget("visibility")
                gust = hget("windgusts_10m")

                tmax = daily.get("temperature_2m_max", [None])[0]
                tmin = daily.get("temperature_2m_min", [None])[0]
                pr_sum = daily.get("precipitation_sum", [None])[0]
                wind_max = daily.get("windspeed_10m_max", [None])[0]

                tips = []
                if pr_sum is not None and pr_sum >= 5:
                    tips.append("осадки: дождевик + чехол на рюкзак, обувь лучше мембранная")
                if gust is not None and gust >= 35:
                    tips.append("сильные порывы: избегай гребней/перевалов")
                if t is not None and t <= 5:
                    tips.append("прохладно: слои (термо + флис + ветровка)")
                if not tips:
                    tips.append("условия нормальные, но возьми ветровку — погода в горах меняется быстро")

                def fmt_vis(m):
                    if m is None:
                        return "-"
                    if m >= 1000:
                        return f"{m/1000:.1f} км"
                    return f"{m} м"

                return (
                    f"Сейчас: {desc}\n"
                    f"🌡 {t}°C (ощущается {feels}°C)\n"
                    f"💧 Влажность: {hum}%\n"
                    f"🌧 Осадки сейчас: {precip_now} мм\n"
                    f"💨 Ветер: {wind} км/ч, порывы: {gust} км/ч\n"
                    f"👁 Видимость: {fmt_vis(vis)}\n\n"
                    f"Сегодня:\n"
                    f"📈 Макс: {tmax}°C\n"
                    f"📉 Мин: {tmin}°C\n"
                    f"🌧 Осадки (сумма): {pr_sum} мм\n"
                    f"💨 Ветер (макс): {wind_max} км/ч\n\n"
                    "💡 Совет:\n" + "\n".join([f"• {x}" for x in tips])
                )
    except:
        return "⚠ Не удалось получить погоду. Попробуйте позже."

@dp.message_handler(lambda m: norm(m.text) == BTN_WEATHER, state="*")
async def weather_menu(message: types.Message, state: FSMContext):
    await state.finish()
    migrate_weather_subs()
    kb = InlineKeyboardMarkup(row_width=2)
    for code, c in CITY_MAP.items():
        kb.insert(InlineKeyboardButton(c["name"], callback_data=f"wcity:{code}"))
    kb.add(
        InlineKeyboardButton("📋 Моя подписка", callback_data="w:my"),
        InlineKeyboardButton("❌ Отписаться", callback_data="w:unsub"),
    )
    await message.answer("⛅ Выберите город:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("wcity:"))
async def weather_city(callback: types.CallbackQuery):
    code = callback.data.split(":", 1)[1]
    text = await get_weather(code)
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Подписаться (10:00 МСК)", callback_data=f"wsub:{code}"),
        InlineKeyboardButton("❌ Отписаться", callback_data="w:unsub")
    )
    await callback.message.answer(f"⛅ Погода — {CITY_MAP[code]['name']}\n\n{text}", reply_markup=kb)
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("wsub:"))
async def weather_sub(callback: types.CallbackQuery):
    code = callback.data.split(":", 1)[1]
    subs = migrate_weather_subs()
    subs[str(callback.from_user.id)] = code
    save_json(SUBS_FILE, subs)
    await callback.answer(f"Подписка ✅ ({CITY_MAP[code]['name']}, 10:00 МСК)")

@dp.callback_query_handler(lambda c: c.data == "w:unsub")
async def weather_unsub(callback: types.CallbackQuery):
    subs = migrate_weather_subs()
    uid = str(callback.from_user.id)
    if uid in subs:
        subs.pop(uid, None)
        save_json(SUBS_FILE, subs)
        await callback.answer("Отписка ✅")
    else:
        await callback.answer("У вас нет подписки")

@dp.callback_query_handler(lambda c: c.data == "w:my")
async def weather_my(callback: types.CallbackQuery):
    subs = migrate_weather_subs()
    code = subs.get(str(callback.from_user.id))
    await callback.answer()
    if not code:
        await callback.message.answer("📋 Подписки нет.")
    else:
        await callback.message.answer(f"📋 Подписка: {CITY_MAP[code]['name']}\n🕙 Автоотправка: 10:00 МСК")

def seconds_until_next_10_msk() -> int:
    tz = pytz.timezone("Europe/Moscow")
    now = datetime.datetime.now(tz)
    target = now.replace(hour=10, minute=0, second=0, microsecond=0)
    if now >= target:
        target = target + datetime.timedelta(days=1)
    return max(1, int((target - now).total_seconds()))

async def auto_weather():
    while True:
        await asyncio.sleep(seconds_until_next_10_msk())
        subs = migrate_weather_subs()
        for uid, code in subs.items():
            try:
                text = await get_weather(code)
                await bot.send_message(int(uid), f"⛅ Погода (10:00 МСК) — {CITY_MAP[code]['name']}\n\n{text}")
            except:
                pass
            await asyncio.sleep(2)

# ============================================================
# AI ГИД (переключатель)
# ============================================================
async def ask_ai(prompt: str):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": AI_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 700
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=25)) as s:
            async with s.post(GROQ_API_URL, headers=headers, json=payload) as r:
                if r.status == 429:
                    return False, "⚠ Лимит запросов AI исчерпан (429)."
                if r.status != 200:
                    return False, f"⚠ Ошибка AI ({r.status})"
                data = await r.json()
                return True, data["choices"][0]["message"]["content"]
    except:
        return False, "⚠ AI временно недоступен."

@dp.message_handler(lambda m: norm(m.text) == BTN_AI, state="*")
async def ai_toggle(message: types.Message, state: FSMContext):
    await state.finish()
    uid = message.from_user.id
    AI_STATE[uid] = not AI_STATE.get(uid, False)
    if AI_STATE[uid]:
        await message.answer(
            "🤖 AI Гид включён.\n\n"
            "Пиши вопрос про КЧР (Домбай/Теберда): куда сходить, маршруты, экипировка.\n"
            "Чтобы выключить — нажми «🤖 AI Гид» ещё раз."
        )
    else:
        await message.answer("✅ AI Гид выключен.")

# ============================================================
# VIP УСЛУГИ - НОВОЕ МЕНЮ С ВЫБОРОМ
# ============================================================
class ServiceForm(StatesGroup):
    category = State()
    name = State()
    desc = State()
    price = State()
    city = State()
    address = State()
    location = State()
    phone = State()
    telegram = State()
    whatsapp = State()
    vk = State()
    instagram = State()
    photo1 = State()
    photo2 = State()

@dp.message_handler(lambda m: norm(m.text) == CANCEL_BTN, state="*")
async def cancel_any(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("❌ Отменено.", reply_markup=main_keyboard(message.from_user.id))

def build_vip_list_keyboard(approved):
    """Создаёт кнопки со списком услуг"""
    kb = InlineKeyboardMarkup(row_width=1)
    for idx, s in enumerate(approved):
        name = s.get('name', 'Без названия')
        category = s.get('category', '')
        # Формат кнопки: "⭐ Название (Категория)"
        button_text = f"⭐ {name}"
        if category:
            button_text += f" — {category}"
        # Обрезаем если слишком длинно
        if len(button_text) > 60:
            button_text = button_text[:57] + "..."
        kb.add(InlineKeyboardButton(button_text, callback_data=f"vip:view:{idx}"))
    return kb

# ГЛАВНЫЙ ПОКАЗ VIP - СПИСОК С КНОПКАМИ
@dp.message_handler(lambda m: norm(m.text) == BTN_VIP_SERVICES, state="*")
async def vip_show_list(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state and current_state.startswith("ServiceForm:"):
        await message.answer(
            "Вы сейчас в процессе добавления VIP услуги.\n"
            "Завершите или нажмите ❌ Отмена.",
            reply_markup=cancel_kb()
        )
        return
    
    await state.finish()
    store = services_store()
    approved = store.get("approved", [])
    
    intro_text = (
        "⭐ <b>VIP Услуги</b>\n\n"
        "Здесь представлены наши партнёры и проверенные сервисы:\n"
        "• Гиды и инструкторы\n"
        "• Трансферы и такси\n"
        "• Прокат снаряжения\n"
        "• Жильё и туры\n\n"
        "🏔 <b>Остальные сервисы — в приложении!</b>\n"
        "👇 Кнопка внизу: <b>📱 Открыть приложение</b>"
    )
    
    if not approved:
        await message.answer(
            intro_text + "\n\n📭 Пока нет активных VIP услуг.",
            parse_mode="HTML"
        )
        return
    
    kb = build_vip_list_keyboard(approved)
    
    await message.answer(
        intro_text + f"\n\n👇 <b>Выберите услугу для подробной информации:</b>",
        parse_mode="HTML",
        reply_markup=kb
    )

# ПРОСМОТР КОНКРЕТНОЙ УСЛУГИ
@dp.callback_query_handler(lambda c: c.data.startswith("vip:view:"))
async def vip_view_service(callback: types.CallbackQuery):
    try:
        idx = int(callback.data.split(":")[2])
    except:
        await callback.answer("Ошибка", show_alert=True)
        return
    
    store = services_store()
    approved = store.get("approved", [])
    
    if idx >= len(approved) or idx < 0:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    
    s = approved[idx]
    text = service_text(s)
    buttons = service_buttons(s, with_back=True)
    photos = s.get("photos", [])
    
    await callback.answer()
    
    # Отправляем услугу
    try:
        if photos and len(photos) > 0:
            try:
                await callback.message.answer_photo(
                    photo=photos[0],
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=buttons
                )
                # Второе фото если есть
                if len(photos) > 1:
                    await asyncio.sleep(0.3)
                    try:
                        await callback.message.answer_photo(
                            photo=photos[1],
                            caption="📷 Дополнительное фото"
                        )
                    except Exception as e:
                        logging.error(f"Ошибка фото 2: {e}")
            except Exception as photo_err:
                logging.error(f"Ошибка фото 1: {photo_err}")
                # Если не получилось с фото — отправляем без него
                await callback.message.answer(text, parse_mode="HTML", reply_markup=buttons)
        else:
            await callback.message.answer(text, parse_mode="HTML", reply_markup=buttons)
    except Exception as e:
        logging.error(f"Ошибка отправки услуги: {e}")
        await callback.message.answer(f"⚠ Ошибка отображения услуги: {str(e)[:100]}")

# ВЕРНУТЬСЯ К СПИСКУ
@dp.callback_query_handler(lambda c: c.data == "vip:list")
async def vip_back_to_list(callback: types.CallbackQuery):
    await callback.answer()
    store = services_store()
    approved = store.get("approved", [])
    
    if not approved:
        await callback.message.answer("📭 Нет активных VIP услуг.")
        return
    
    kb = build_vip_list_keyboard(approved)
    await callback.message.answer(
        "⭐ <b>VIP Услуги</b>\n\n👇 Выберите услугу:",
        parse_mode="HTML",
        reply_markup=kb
    )

# ============================================================
# ДОБАВЛЕНИЕ VIP УСЛУГИ
# ============================================================
@dp.message_handler(lambda m: norm(m.text) == BTN_ADD_VIP, state="*")
async def vip_add_start(message: types.Message, state: FSMContext):
    await state.finish()
    store = services_store()
    limit = get_services_limit()
    if len(store.get("approved", [])) >= limit:
        await message.answer(f"❌ Лимит VIP услуг достигнут ({limit}).")
        return
    if str(message.from_user.id) in approved_owner_ids(store):
        await message.answer("❌ У вас уже есть одобренная VIP услуга. Если нужно изменить — напишите администратору.")
        return
    
    await message.answer(
        "📝 <b>Добавление VIP услуги</b>\n\n"
        "⚠ <b>Важно:</b>\n"
        "• Заполняйте поля по порядку\n"
        "• Отправляйте ОДНО сообщение за раз\n"
        "• Не отправляйте несколько фото сразу\n"
        "• Для пропуска нажмите «⏭ Пропустить»\n\n"
        "Введите категорию (например: Гид / Трансфер / Прокат / Жильё):",
        parse_mode="HTML",
        reply_markup=cancel_kb()
    )
    await ServiceForm.category.set()

@dp.message_handler(state=ServiceForm.category)
async def vip_category(message: types.Message, state: FSMContext):
    cat = norm(message.text)
    if len(cat) < 2:
        await message.answer("❌ Категория слишком короткая. Введите нормально.")
        return
    await state.update_data(category=cat)
    await message.answer("Введите название услуги:", reply_markup=cancel_kb())
    await ServiceForm.next()

@dp.message_handler(state=ServiceForm.name)
async def vip_name(message: types.Message, state: FSMContext):
    name = norm(message.text)
    if len(name) < 2:
        await message.answer("❌ Название слишком короткое.")
        return
    await state.update_data(name=name)
    await message.answer("Введите описание услуги:", reply_markup=cancel_kb())
    await ServiceForm.next()

@dp.message_handler(state=ServiceForm.desc)
async def vip_desc(message: types.Message, state: FSMContext):
    await state.update_data(desc=norm(message.text))
    await message.answer("Введите стоимость (например: 5000₽ или 'договорная'):", reply_markup=cancel_kb())
    await ServiceForm.next()

@dp.message_handler(state=ServiceForm.price)
async def vip_price(message: types.Message, state: FSMContext):
    await state.update_data(price=norm(message.text))
    await message.answer("Введите город (например: Домбай, Теберда):", reply_markup=cancel_kb())
    await ServiceForm.next()

@dp.message_handler(state=ServiceForm.city)
async def vip_city(message: types.Message, state: FSMContext):
    await state.update_data(city=norm(message.text))
    await message.answer("Введите адрес:", reply_markup=cancel_kb())
    await ServiceForm.next()

@dp.message_handler(state=ServiceForm.address)
async def vip_address(message: types.Message, state: FSMContext):
    await state.update_data(address=norm(message.text))
    await message.answer("📍 Отправьте геолокацию или нажмите «⏭ Пропустить».", reply_markup=skip_kb())
    await ServiceForm.next()

@dp.message_handler(content_types=types.ContentType.LOCATION, state=ServiceForm.location)
async def vip_location_geo(message: types.Message, state: FSMContext):
    loc = message.location
    await state.update_data(location={"lat": loc.latitude, "lon": loc.longitude})
    await message.answer("📞 Введите телефон:", reply_markup=skip_kb())
    await ServiceForm.next()

@dp.message_handler(state=ServiceForm.location)
async def vip_location_skip(message: types.Message, state: FSMContext):
    if norm(message.text) == SKIP_BTN:
        await message.answer("📞 Введите телефон:", reply_markup=skip_kb())
        await ServiceForm.next()
    else:
        await message.answer("⚠ Либо отправьте геолокацию, либо нажмите «⏭ Пропустить».", reply_markup=skip_kb())

@dp.message_handler(state=ServiceForm.phone)
async def vip_phone(message: types.Message, state: FSMContext):
    if norm(message.text) != SKIP_BTN:
        await state.update_data(phone=norm(message.text))
    await message.answer("✈ Введите Telegram (@username):", reply_markup=skip_kb())
    await ServiceForm.next()

@dp.message_handler(state=ServiceForm.telegram)
async def vip_tg(message: types.Message, state: FSMContext):
    if norm(message.text) != SKIP_BTN:
        await state.update_data(telegram=norm(message.text))
    await message.answer("📱 Введите номер WhatsApp:", reply_markup=skip_kb())
    await ServiceForm.next()

@dp.message_handler(state=ServiceForm.whatsapp)
async def vip_wa(message: types.Message, state: FSMContext):
    if norm(message.text) != SKIP_BTN:
        await state.update_data(whatsapp=norm(message.text))
    await message.answer("🔵 Введите ссылку на VK (http...):", reply_markup=skip_kb())
    await ServiceForm.next()

@dp.message_handler(state=ServiceForm.vk)
async def vip_vk(message: types.Message, state: FSMContext):
    if norm(message.text) != SKIP_BTN:
        await state.update_data(vk=norm(message.text))
    await message.answer("📷 Введите ссылку на Instagram (http...):", reply_markup=skip_kb())
    await ServiceForm.next()

@dp.message_handler(state=ServiceForm.instagram)
async def vip_inst(message: types.Message, state: FSMContext):
    if norm(message.text) != SKIP_BTN:
        await state.update_data(instagram=norm(message.text))
    await message.answer(
        "📷 <b>Отправьте ОДНО фото</b> (или нажмите «⏭ Пропустить»)\n\n"
        "⚠ Не отправляйте несколько фото сразу!",
        parse_mode="HTML",
        reply_markup=skip_kb()
    )
    await ServiceForm.next()

@dp.message_handler(content_types=types.ContentType.PHOTO, state=ServiceForm.photo1)
async def vip_photo1_image(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo1=photo_id)
    await message.answer(
        "✅ Первое фото получено!\n\n"
        "📷 Отправьте ОДНО второе фото (или нажмите «⏭ Пропустить»)",
        reply_markup=skip_kb()
    )
    await ServiceForm.next()

@dp.message_handler(state=ServiceForm.photo1)
async def vip_photo1_skip(message: types.Message, state: FSMContext):
    if norm(message.text) == SKIP_BTN:
        await message.answer(
            "📷 Отправьте ОДНО второе фото (или нажмите «⏭ Пропустить»)",
            reply_markup=skip_kb()
        )
        await ServiceForm.next()
    else:
        await message.answer("⚠ Пожалуйста, отправьте ОДНО фото или нажмите «⏭ Пропустить».", reply_markup=skip_kb())

@dp.message_handler(content_types=types.ContentType.PHOTO, state=ServiceForm.photo2)
async def vip_photo2_image(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo2=photo_id)
    await message.answer("✅ Второе фото получено! Обрабатываем...")
    await vip_finalize(message, state)

@dp.message_handler(state=ServiceForm.photo2)
async def vip_photo2_skip(message: types.Message, state: FSMContext):
    if norm(message.text) == SKIP_BTN:
        await vip_finalize(message, state)
    else:
        await message.answer("⚠ Пожалуйста, отправьте ОДНО фото или нажмите «⏭ Пропустить».", reply_markup=skip_kb())

async def vip_finalize(message: types.Message, state: FSMContext):
    """Завершение добавления VIP услуги"""
    data = await state.get_data()
    
    photos = []
    if data.get("photo1"):
        photos.append(data["photo1"])
    if data.get("photo2"):
        photos.append(data["photo2"])
    
    service = {
        "owner_id": message.from_user.id,
        "category": data.get("category", ""),
        "name": data.get("name", ""),
        "desc": data.get("desc", ""),
        "price": data.get("price", ""),
        "city": data.get("city", ""),
        "address": data.get("address", ""),
        "location": data.get("location"),
        "phone": data.get("phone", ""),
        "telegram": data.get("telegram", ""),
        "whatsapp": data.get("whatsapp", ""),
        "vk": data.get("vk", ""),
        "instagram": data.get("instagram", ""),
        "photos": photos,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    
    store = services_store()
    store["pending"].append(service)
    save_json(SERVICES_FILE, store)
    
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Одобрить", callback_data=f"s:approve:{service['owner_id']}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"s:reject:{service['owner_id']}")
    )
    
    admin_text = "📩 Новая VIP заявка:\n\n" + service_text(service)
    
    if photos:
        try:
            await bot.send_photo(
                ADMIN_ID,
                photo=photos[0],
                caption=admin_text,
                parse_mode="HTML",
                reply_markup=kb
            )
            if len(photos) > 1:
                await bot.send_photo(ADMIN_ID, photo=photos[1], caption="📷 Фото 2")
        except Exception as e:
            logging.error(f"Ошибка отправки фото админу: {e}")
            await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML", reply_markup=kb)
    else:
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML", reply_markup=kb)
    
    await message.answer("✅ Заявка отправлена на модерацию!", reply_markup=main_keyboard(message.from_user.id))
    await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith("s:approve:"))
async def vip_approve(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    try:
        owner_id = int(callback.data.split(":")[2])
    except:
        await callback.answer("Ошибка данных", show_alert=True)
        return
    store = services_store()
    limit = get_services_limit()
    if len(store.get("approved", [])) >= limit:
        await callback.answer(f"Лимит VIP уже достигнут ({limit})", show_alert=True)
        return
    if str(owner_id) in approved_owner_ids(store):
        store["pending"] = [x for x in store.get("pending", []) if int(x.get("owner_id", -1)) != owner_id]
        save_json(SERVICES_FILE, store)
        await callback.answer("У владельца уже есть VIP услуга.", show_alert=True)
        return
    pending = store.get("pending", [])
    target = None
    for s in pending:
        if int(s.get("owner_id", -1)) == owner_id:
            target = s
            break
    if not target:
        await callback.answer("Заявка не найдена", show_alert=True)
        return
    store["pending"] = [x for x in pending if int(x.get("owner_id", -1)) != owner_id]
    store["approved"].append(target)
    save_json(SERVICES_FILE, store)
    await callback.answer("Одобрено ✅")
    try:
        await bot.send_message(owner_id, f"✅ VIP услуга одобрена и опубликована! (Автоудаление через {get_service_ttl_days()} дней)")
    except:
        pass

@dp.callback_query_handler(lambda c: c.data.startswith("s:reject:"))
async def vip_reject(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    try:
        owner_id = int(callback.data.split(":")[2])
    except:
        await callback.answer("Ошибка данных", show_alert=True)
        return
    store = services_store()
    store["pending"] = [x for x in store.get("pending", []) if int(x.get("owner_id", -1)) != owner_id]
    save_json(SERVICES_FILE, store)
    await callback.answer("Отклонено ❌")

# ============================================================
# АВТОУДАЛЕНИЕ VIP (TTL)
# ============================================================
def _parse_iso(dt_str: str):
    try:
        return datetime.datetime.fromisoformat(dt_str)
    except:
        return None

async def auto_prune_services():
    while True:
        try:
            ttl_days = get_service_ttl_days()
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=ttl_days)
            store = services_store()
            approved = store.get("approved", [])
            keep, removed = [], []
            for s in approved:
                created = _parse_iso(s.get("created_at", ""))
                if created and created < cutoff:
                    removed.append(s)
                else:
                    keep.append(s)
            if removed:
                store["approved"] = keep
                save_json(SERVICES_FILE, store)
        except:
            pass
        await asyncio.sleep(3600)

# ============================================================
# АДМИН-ПАНЕЛЬ + УПРАВЛЕНИЕ
# ============================================================
@dp.message_handler(lambda m: norm(m.text) == BTN_ADMIN_PANEL, state="*")
async def admin_panel(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        "⚙ Админ-панель\n\n"
        f"⭐ VIP лимит: {get_services_limit()}\n"
        f"⏳ VIP срок: {get_service_ttl_days()} дней\n\n"
        "Команды:\n"
        "/files — пути файлов\n"
        "/vipdebug — проверка VIP",
        reply_markup=admin_keyboard()
    )

@dp.message_handler(lambda m: norm(m.text) == A_BACK, state="*")
async def admin_back(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Главное меню:", reply_markup=main_keyboard(message.from_user.id))

# АДМИН: УПРАВЛЕНИЕ VIP - список с кнопками удаления
@dp.message_handler(lambda m: norm(m.text) == A_MANAGE_VIP, state="*")
async def admin_manage_vip(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id != ADMIN_ID:
        return
    store = services_store()
    approved = store.get("approved", [])
    if not approved:
        await message.answer("Нет опубликованных VIP услуг.", reply_markup=admin_keyboard())
        return
    
    # Создаём меню с кнопками - название + удалить
    kb = InlineKeyboardMarkup(row_width=2)
    for idx, s in enumerate(approved):
        name = s.get('name', 'Без названия')
        btn_view = InlineKeyboardButton(f"👁 {name[:30]}", callback_data=f"adm:view:{idx}")
        btn_del = InlineKeyboardButton("❌ Удалить", callback_data=f"adm:del:{s.get('owner_id')}")
        kb.row(btn_view, btn_del)
    
    await message.answer(
        f"⭐ <b>VIP услуги ({len(approved)}):</b>\n\n"
        "👁 — просмотреть\n"
        "❌ — удалить",
        parse_mode="HTML",
        reply_markup=kb
    )

# АДМИН: ПРОСМОТР УСЛУГИ
@dp.callback_query_handler(lambda c: c.data.startswith("adm:view:"))
async def admin_view_service(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    try:
        idx = int(callback.data.split(":")[2])
    except:
        await callback.answer("Ошибка", show_alert=True)
        return
    
    store = services_store()
    approved = store.get("approved", [])
    
    if idx >= len(approved):
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    
    s = approved[idx]
    text = service_text(s) + f"\n\n👤 owner_id: {s.get('owner_id')}"
    photos = s.get("photos", [])
    
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("❌ Удалить эту услугу", callback_data=f"adm:del:{s.get('owner_id')}")
    )
    
    await callback.answer()
    
    try:
        if photos:
            try:
                await callback.message.answer_photo(
                    photo=photos[0],
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=kb
                )
                if len(photos) > 1:
                    await callback.message.answer_photo(photo=photos[1], caption="📷 Фото 2")
            except:
                await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
        else:
            await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        logging.error(f"Ошибка просмотра админом: {e}")
        await callback.message.answer(f"⚠ Ошибка: {str(e)[:100]}")

# АДМИН: УДАЛЕНИЕ
@dp.callback_query_handler(lambda c: c.data.startswith("adm:del:"))
async def admin_delete_vip(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    try:
        owner_id = int(callback.data.split(":")[2])
    except:
        await callback.answer("Ошибка данных", show_alert=True)
        return
    store = services_store()
    store["approved"] = [s for s in store.get("approved", []) if int(s.get("owner_id", -1)) != owner_id]
    save_json(SERVICES_FILE, store)
    await callback.answer("Удалено ✅", show_alert=True)
    try:
        await bot.send_message(owner_id, "❌ Ваша VIP услуга удалена администратором.")
    except:
        pass

class AdminEdit(StatesGroup):
    limit = State()
    ttl = State()

@dp.message_handler(lambda m: norm(m.text) == A_SET_LIMIT)
async def admin_set_limit_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(f"Введите новый лимит VIP (сейчас {get_services_limit()}):")
    await AdminEdit.limit.set()

@dp.message_handler(state=AdminEdit.limit)
async def admin_set_limit_finish(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.finish()
        return
    try:
        n = int(norm(message.text))
        if n < 1:
            raise ValueError()
        set_services_limit(n)
        await message.answer(f"✅ Лимит VIP установлен: {n}", reply_markup=admin_keyboard())
        await state.finish()
    except:
        await message.answer("❌ Введите целое число >= 1")

@dp.message_handler(lambda m: norm(m.text) == A_SET_TTL)
async def admin_set_ttl_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(f"Введите срок VIP в днях (сейчас {get_service_ttl_days()}):")
    await AdminEdit.ttl.set()

@dp.message_handler(state=AdminEdit.ttl)
async def admin_set_ttl_finish(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.finish()
        return
    try:
        n = int(norm(message.text))
        if n < 1:
            raise ValueError()
        set_service_ttl_days(n)
        await message.answer(f"✅ Срок VIP установлен: {n} дней", reply_markup=admin_keyboard())
        await state.finish()
    except:
        await message.answer("❌ Введите целое число >= 1")

# ================= АДМИН: РАССЫЛКА =================
@dp.message_handler(lambda m: norm(m.text) == A_BROADCAST)
async def broadcast_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Введите команду:\n/send Ваш текст", reply_markup=admin_keyboard())

@dp.message_handler(commands=["send"])
async def send(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.get_args().strip()
    if not text:
        await message.answer("Использование: /send текст")
        return
    users = load_json(USERS_FILE, [])
    sent = 0
    failed = 0
    for uid in users:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except:
            failed += 1
    try:
        await bot.send_message(CHANNEL_ID, text)
    except:
        pass
    await message.answer(f"✅ Отправлено: {sent}\n❌ Ошибки: {failed}", reply_markup=admin_keyboard())

# ================= АДМИН: СТАТИСТИКА =================
@dp.message_handler(lambda m: norm(m.text) == A_STATS)
async def stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    users = load_json(USERS_FILE, [])
    subs = migrate_weather_subs()
    limits = load_json(LIMITS_FILE, {})
    store = services_store()
    today = datetime.date.today().isoformat()
    today_count = sum(int(v.get("count", 0)) for v in limits.values() if v.get("date") == today)
    await message.answer(
        "📊 Статистика:\n\n"
        f"👥 Пользователей: {len(users)}\n"
        f"⛅ Подписки на погоду: {len(subs)}\n"
        f"🤖 AI запросов сегодня: {today_count}\n"
        f"⭐ VIP (одобрено): {len(store.get('approved', []))}\n"
        f"📩 VIP (на модерации): {len(store.get('pending', []))}\n\n"
        f"⚙ VIP лимит: {get_services_limit()}\n"
        f"⏳ VIP срок: {get_service_ttl_days()} дней",
        reply_markup=admin_keyboard()
    )

# ============================================================
# ОБЩИЙ ТЕКСТ (AI / fallback)
# ============================================================
@dp.message_handler()
async def text_handler(message: types.Message):
    add_user(message.from_user.id)
    uid = message.from_user.id
    text = (message.text or "").strip()

    if AI_STATE.get(uid):
        ok_limit, _ = check_limit(uid)
        if not ok_limit:
            await message.answer("❌ Дневной лимит AI исчерпан. Лимит обновится завтра.")
            return

        await bot.send_chat_action(message.chat.id, types.ChatActions.TYPING)

        # ВАЖНО: всегда отвечаем пользователю, даже если ok=False
        ok, reply = await ask_ai(text)

        if ok:
            use_limit(uid)

        # если провайдер/квота закончились — можно автоматом выключать AI режим
        if reply == "Лимит запросов исчерпан":
            AI_STATE.pop(uid, None)

        await message.answer(reply)
        return

    await message.answer("Выберите раздел в меню или нажмите /start")

import os

HEALTHCHECK_INTERVAL = 60
HEALTHCHECK_FAILS = 3

async def telegram_healthcheck():
    fails = 0
    while True:
        try:
            await asyncio.wait_for(bot.get_me(), timeout=10)
            fails = 0
        except Exception as e:
            fails += 1
            logging.error("Healthcheck fail %s/%s: %s", fails, HEALTHCHECK_FAILS, e)
            if fails >= HEALTHCHECK_FAILS:
                os._exit(1)  # systemd перезапустит
        await asyncio.sleep(HEALTHCHECK_INTERVAL)

# ================= STARTUP =================
async def on_startup(_):
    ensure_json_file(USERS_FILE, [])
    ensure_json_file(SUBS_FILE, {})
    ensure_json_file(LIMITS_FILE, {})
    ensure_json_file(SERVICES_FILE, {"pending": [], "approved": []})
    ensure_json_file(SETTINGS_FILE, {"services_limit": 5, "service_ttl_days": 30})
    load_settings()
    services_store()
    migrate_weather_subs()
    asyncio.create_task(auto_weather())
    asyncio.create_task(auto_prune_services())

# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, timeout=30, on_startup=on_startup)