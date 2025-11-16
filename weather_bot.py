import sqlite3
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command

API_KEY = '5af718916f321b457560be9c34e12301'
BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'

CENTRAL_ASIA = {
    "🇺🇿 O'zbekiston": [
        "Tashkent", "Andijan", "Bukhara", "Fergana", "Jizzakh",
        "Karakalpakstan", "Urganch", "Namangan", "Navoi", "Samarkand",
        "Sirdaryo", "Termez", "Qashqadaryo"
    ],
    "🇰🇿 Qozog'iston": [
        "Almaty", "Nur-Sultan", "Shymkent", "Karaganda", "Aktobe",
        "Pavlodar", "Kostanay", "Taraz", "Atyrau", "Kyzylorda"
    ],
    "🇰🇬 Qirg'iziston": [
        "Bishkek", "Osh", "Jalal-Abad", "Karakol", "Naryn",
        "Talas", "Batken"
    ],
    "🇹🇯 Tojikiston": [
        "Dushanbe", "Khujand", "Kulob", "Bokhtar", "Istaravshan"
    ],
    "🇹🇲 Turkmaniston": [
        "Ashgabat", "Turkmenabat", "Mary", "Balkanabat", "Dashoguz"
    ]
}


# --- SQLite bazasi ---
def setup_database():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_date TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user_to_database(user_id, username, first_name):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO users (id, username, first_name, joined_date)
        VALUES (?, ?, ?, datetime('now'))
    """, (user_id, username, first_name))
    conn.commit()
    conn.close()

def get_user_count():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# --- Bot sozlash ---
BOT_TOKEN = "8253946191:AAHVZBwPCTKXaXvM5KlTtIPj735_yKnlJbY"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- /start ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    add_user_to_database(message.from_user.id, message.from_user.username, message.from_user.first_name)

    keyboard = InlineKeyboardBuilder()
    keys = list(CENTRAL_ASIA.keys())
    for i in range(0, len(keys), 2):
        row = [InlineKeyboardButton(text=keys[i], callback_data=keys[i])]
        if i + 1 < len(keys):
            row.append(InlineKeyboardButton(text=keys[i+1], callback_data=keys[i+1]))
        keyboard.row(*row)
    await message.answer("🌏 <b>Assalomu alaykum!</b> O'rta Osiyo davlatlaridan birini tanlang:", 
                         reply_markup=keyboard.as_markup(), parse_mode="HTML")

# --- /statistics (faqat admin) ---
ADMIN_ID = 6756842683

@dp.message(Command("statistics"))
async def cmd_statistics(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        count = get_user_count()
        await message.answer(f"Botda hozirda {count} foydalanuvchi bor.")
    else:
        await message.answer("Bu buyruq faqat admin uchun.")

# --- Callback query handler ---

@dp.callback_query()
async def handle_buttons(callback: types.CallbackQuery):
    data = callback.data

    if data in CENTRAL_ASIA:  # Davlat tanlandi
        regions = CENTRAL_ASIA[data]
        keyboard = InlineKeyboardBuilder()
        for i in range(0, len(regions), 2):
            row = [InlineKeyboardButton(text=regions[i], callback_data=regions[i])]
            if i+1 < len(regions):
                row.append(InlineKeyboardButton(text=regions[i+1], callback_data=regions[i+1]))
            keyboard.row(*row)
        keyboard.row(InlineKeyboardButton(text="⬅️ Boshqa davlat tanlash", callback_data="restart"))
        await callback.message.edit_text(f"🌍 <b>{data}</b> davlatini tanladingiz. 🌟 Endi viloyatni tanlang:",
                                         reply_markup=keyboard.as_markup(), parse_mode="HTML")

    elif data in sum(CENTRAL_ASIA.values(), []):  # Viloyat tanlandi
        async with aiohttp.ClientSession() as session:
            async with session.get(BASE_URL, params={'q': data, 'appid': API_KEY, 'units': 'metric'}) as resp:
                print(resp)
                if resp.status == 200:
                    info = await resp.json()
                    print(info)
                    text = (
                        f"📍 <b>Viloyat:</b> {info['name']}\n"
                        f"🌡️ <b>Temperatura:</b> {info['main']['temp']}°C\n"
                        f"🌥️ <b>Ob-havo:</b> {info['weather'][0]['description']}\n"
                        f"💧 <b>Namlik:</b> {info['main']['humidity']}%\n"
                        f"🌬️ <b>Shamol tezligi:</b> {info['wind']['speed']} m/s"
                    )
                    keyboard = InlineKeyboardBuilder()
                    keyboard.row(InlineKeyboardButton(text="⬅️ Boshqa davlat tanlash", callback_data="restart"))
                    await callback.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
                else:
                    await callback.message.edit_text("❌ Xatolik yuz berdi yoki viloyat topilmadi.")

    elif data == "restart":
        await cmd_start(callback.message)

    await callback.answer()


# --- Main ---
if __name__ == "__main__":
    setup_database()
    import asyncio
    asyncio.run(dp.start_polling(bot))
