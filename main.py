import telebot
from telebot import types
import json
import datetime
import os

# ══════════════════════════════════════════════
#                  SOZLAMALAR
# ══════════════════════════════════════════════
TOKEN          = '8659508590:AAG4yEGt9uE0nc_zW91wcHldtI3kjzefJ-4'
ADMIN_ID       = 8159211308
CHANNELS       = ["@anibratt"]
HENTAI_LINK    = "https://t.me/anibratt" 

# Janrlar ro'yxati
GENRES = ["Action ⚔️", "Romantika ❤️", "Sarguzasht 🗺", "Komediya 😂"]

# ══════════════════════════════════════════════
#           FAYL-ASOSLI DATABASE (MongoDB o'rniga)
# ══════════════════════════════════════════════
DATA_FILE = "bot_data.json"

def load_data():
    """Fayldan ma'lumotlarni yuklash"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"anime": [], "users": [], "status": []}

def save_data(data):
    """Ma'lumotlarni faylga saqlash"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Bot sozlamasi
bot = telebot.TeleBot(TOKEN)
user_state = {}

# ══════════════════════════════════════════════
#              YORDAMCHI FUNKSIYALAR
# ══════════════════════════════════════════════
def is_premium(uid):
    """Premium foydalanuvchini tekshirish"""
    if uid == ADMIN_ID: 
        return True
    
    data = load_data()
    for user in data.get('status', []):
        if user.get('user_id') == uid and user.get('premium'):
            if user.get('expiry') == "forever":
                return True
            return user.get('expiry') > datetime.date.today().strftime("%Y-%m-%d")
    return False

def main_menu(uid):
    """Asosiy menyu"""
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add("🎬 Anime izlash", "📂 Janrlar")
    m.add("📋 Animelar ro'yxati", "📞 Admin bilan bog'lanish")
    m.add("💎 Premium va Trend", "👤 Profil")
    
    if is_premium(uid):
        m.add("📝 Anime buyurtma", "🔞 Hentai bo'limi")
    if uid == ADMIN_ID:
        m.row("🛠 Admin paneli", "📊 Statistika")
    return m

# ══════════════════════════════════════════════
#                JANRLAR BO'LIMI
# ══════════════════════════════════════════════
@bot.message_handler(func=lambda m: m.text == "📂 Janrlar")
def genre_menu(message):
    uid = message.from_user.id
    if not is_premium(uid):
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("💎 Premium sotib olish", callback_data="buy_premium"))
        bot.send_message(message.chat.id, "❌ <b>Janrlar bo'limi faqat Premium foydalanuvchilar uchun!</b>\n\nMarhamat, premium tariflarimiz bilan tanishing:", reply_markup=m, parse_mode="HTML")
        return

    m = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(g, callback_data=f"genre_{g}") for g in GENRES]
    m.add(*btns)
    bot.send_message(message.chat.id, "📂 Janrni tanlang:", reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data.startswith("genre_"))
def show_genre_animes(call):
    """Janr bo'yicha animelarni ko'rsatish"""
    genre = call.data.split("_", 1)[1]
    data = load_data()
    animes = [a for a in data['anime'] if a.get('genre') == genre]
    
    if not animes:
        bot.answer_callback_query(call.id, f"{genre} janrida hozircha anime yo'q.")
        return
    
    m = types.InlineKeyboardMarkup()
    for a in animes:
        m.add(types.InlineKeyboardButton(a['name'], callback_data=f"show_{a['code']}"))
    
    bot.edit_message_text(f"📂 <b>{genre}</b> janridagi animelar:", call.message.chat.id, call.message.message_id, reply_markup=m, parse_mode="HTML")

# ══════════════════════════════════════════════
#         ADMIN: JANR BILAN ANIME QO'SHISH
# ══════════════════════════════════════════════
@bot.callback_query_handler(func=lambda call: call.data == "new_anime")
def admin_add_step1(call):
    user_state[call.from_user.id] = {'step': 'get_photo'}
    bot.send_message(call.message.chat.id, "📸 Anime uchun rasm yuboring:")

@bot.message_handler(content_types=['photo'], func=lambda m: user_state.get(m.from_user.id, {}).get('step') == 'get_photo')
def admin_add_step2(message):
    user_state[message.from_user.id].update({'photo': message.photo[-1].file_id, 'step': 'get_genre'})
    
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    m.add(*GENRES)
    bot.send_message(message.chat.id, "📂 Animeny janrini tanlang:", reply_markup=m)

@bot.message_handler(func=lambda m: user_state.get(m.from_user.id, {}).get('step') == 'get_genre' and m.text in GENRES)
def admin_add_step3(message):
    user_state[message.from_user.id].update({'genre': message.text, 'step': 'get_name_code'})
    bot.send_message(message.chat.id, "📝 Endi nomi va kodini yuboring (Masalan: Naruto | 707):")

@bot.message_handler(func=lambda m: user_state.get(m.from_user.id, {}).get('step') == 'get_name_code')
def admin_add_step4(message):
    try:
        name, code = [x.strip() for x in message.text.split('|')]
        data = load_data()
        data['anime'].append({
            "code": code, 
            "name": name, 
            "photo": user_state[message.from_user.id]['photo'], 
            "genre": user_state[message.from_user.id]['genre'],
            "parts": []
        })
        save_data(data)
        bot.send_message(message.chat.id, f"✅ <b>{name}</b> ({user_state[message.from_user.id]['genre']}) bazaga qo'shildi!", reply_markup=main_menu(message.from_user.id), parse_mode="HTML")
        del user_state[message.from_user.id]
    except:
        bot.send_message(message.chat.id, "❌ Xato! Format: Nomi | Kod")

# ══════════════════════════════════════════════
#              START BUYRUG'I
# ══════════════════════════════════════════════
@bot.message_handler(commands=['start'])
def start(message):
    """Bot ishga tushgani ko'rsatish"""
    uid = message.from_user.id
    data = load_data()
    
    # Foydalanuvchini bazaga qo'shish
    if not any(u.get('user_id') == uid for u in data['users']):
        data['users'].append({
            'user_id': uid,
            'username': message.from_user.username or "Nomatsiz",
            'joined': datetime.date.today().strftime("%Y-%m-%d")
        })
        save_data(data)
    
    bot.send_message(uid, f"👋 Salom, <b>{message.from_user.first_name}</b>!\n\n🎬 <b>Anime Bot</b> ga xush kelibsiz!\n\nMenga anime, manga va hentai haqida so'rasiz va men sizga tavsiya qilaman.", 
                     reply_markup=main_menu(uid), parse_mode="HTML")

# ══════════════════════════════════════════════
#              STATISTIKA (ADMIN)
# ══════════════════════════════════════════════
@bot.message_handler(func=lambda m: m.text == "📊 Statistika" and m.from_user.id == ADMIN_ID)
def show_stats(message):
    data = load_data()
    anime_count = len(data['anime'])
    user_count = len(data['users'])
    
    stats_text = f"""
📊 <b>BOT STATISTIKASI</b>

🎬 Animelar soni: <b>{anime_count}</b>
👥 Foydalanuvchilar soni: <b>{user_count}</b>
📅 Bugun: {datetime.date.today().strftime("%Y-%m-%d")}
    """
    
    bot.send_message(message.chat.id, stats_text, parse_mode="HTML", reply_markup=main_menu(message.from_user.id))

# ══════════════════════════════════════════════
#              BOT ISHGA TUSHIRISH
# ══════════════════════════════════════════════
if __name__ == "__main__":
    print("✅ Bot ishga tushdi!")
    print(f"📊 Ma'lumotlar: {len(load_data()['anime'])} anime, {len(load_data()['users'])} foydalanuvchi")
    bot.infinity_polling()
