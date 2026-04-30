import telebot
from telebot import types
import pymongo
import datetime

# ══════════════════════════════════════════════
#                  SOZLAMALAR
# ══════════════════════════════════════════════
TOKEN          = '8659508590:AAG4yEGt9uE0nc_zW91wcHldtI3kjzefJ-4'
MONGO_URL      = "mongodb+srv://nurdiyor:CKJ5D40FtZ79IvSd@cluster0.nvjsvlg.mongodb.net/?appName=Cluster0"
ADMIN_ID       = 8159211308
CHANNELS       = ["@anibratt"]
HENTAI_LINK    = "https://t.me/anibratt" 

# Janrlar ro'yxati
GENRES = ["Action ⚔️", "Romantika ❤️", "Sarguzasht 🗺", "Komediya 😂"]

# ══════════════════════════════════════════════
#              BAZA VA BOTNI SOZLASH
# ══════════════════════════════════════════════
client = pymongo.MongoClient(MONGO_URL)
db = client['anibrat_db']
anime_col = db['anime']
users_col = db['users']
status_col = db['status']

bot = telebot.TeleBot(TOKEN)
user_state = {}

# ══════════════════════════════════════════════
#              YORDAMCHI FUNKSIYALAR
# ══════════════════════════════════════════════
def is_premium(uid):
    if uid == ADMIN_ID: return True
    user = status_col.find_one({"user_id": uid, "premium": True})
    if user:
        if user.get('expiry') == "forever": return True
        return user.get('expiry') > datetime.date.today().strftime("%Y-%m-%d")
    return False

def main_menu(uid):
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
    genre = call.data.split("_")[1]
    animes = list(anime_col.find({"genre": genre}))
    
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
        anime_col.insert_one({
            "code": code, 
            "name": name, 
            "photo": user_state[message.from_user.id]['photo'], 
            "genre": user_state[message.from_user.id]['genre'],
            "parts": []
        })
        bot.send_message(message.chat.id, f"✅ <b>{name}</b> ({user_state[message.from_user.id]['genre']}) bazaga qo'shildi!", reply_markup=main_menu(message.from_user.id), parse_mode="HTML")
        del user_state[message.from_user.id]
    except:
        bot.send_message(message.chat.id, "❌ Xato! Format: Nomi | Kod")

# ... (Kodingni qolgan qismlari: start, qism qo'shish, to'lovlar - boyagi kod bilan bir xil qoladi)

bot.infinity_polling()

