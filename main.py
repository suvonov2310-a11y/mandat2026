import asyncio
import logging
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ==========================================
# ⚙️ ASOSIY SOZLAMALAR
# ==========================================
BOT_TOKEN = "8798060376:AAH2RkSzM50-8iC6KnT_Oq8yMBws1W-ZpH0" 
ADMIN_ID = 2024143361  # O'zingizning Telegram ID raqamingizni yozing

CHANNEL_USERNAME = "@ozbemas_agar"
PARTNER_BOT = "@ChatAl_gptBot"
TEST_BOT = "@Abituriyent_2026Bot"
DB_NAME = "abituriyentlar.db"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==========================================
# 🗄 ASINXRON MA'LUMOTLAR BAZASI
# ==========================================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
        await db.commit()

# ==========================================
# 🚥 FSM (HOLATLAR)
# ==========================================
class CalcState(StatesGroup):
    majburiy = State()
    mutaxassislik_1 = State()
    mutaxassislik_2 = State()

class MandatState(StatesGroup):
    waiting_for_id = State()

# ==========================================
# 📊 O'TISH BALLARI BAZASI
# ==========================================
SCORES_DB = {
    "tdiu": {
        "name": "Toshkent Davlat Iqtisodiyot Universiteti (TDIU)",
        "yonalishlar": [
            {"name": "Iqtisodiyot (tarmoqlar bo'yicha)", "grant": 178.5, "kontrakt": 140.2},
            {"name": "Buxgalteriya hisobi va audit", "grant": 175.0, "kontrakt": 135.5},
            {"name": "Sun'iy intellekt", "grant": 168.4, "kontrakt": 130.0}
        ]
    },
    "tatu": {
        "name": "Toshkent Axborot Texnologiyalari Universiteti (TATU)",
        "yonalishlar": [
            {"name": "Dasturiy injiniring", "grant": 180.5, "kontrakt": 148.0},
            {"name": "Axborot xavfsizligi", "grant": 176.2, "kontrakt": 142.5}
        ]
    },
    "ozmu": {
        "name": "O'zbekiston Milliy Universiteti (O'zMU)",
        "yonalishlar": [
            {"name": "Matematika", "grant": 165.2, "kontrakt": 120.4},
            {"name": "Fizika", "grant": 158.0, "kontrakt": 115.0}
        ]
    }
}

# ==========================================
# 🎛 KLAVIATURALAR
# ==========================================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧮 Ball hisoblagich"), KeyboardButton(text="📊 O'tish ballari")],
        [KeyboardButton(text="🏢 Kvotalar"), KeyboardButton(text="📝 Online Blok Test")],
        [KeyboardButton(text="🔍 MANDAT TEKSHIRISH (ID)")]
    ],
    resize_keyboard=True
)

def get_sub_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
        ]
    )

def get_otm_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏢 TDIU", callback_data="score_tdiu"),
             InlineKeyboardButton(text="💻 TATU", callback_data="score_tatu")],
            [InlineKeyboardButton(text="🏛 O'zMU", callback_data="score_ozmu")]
        ]
    )

# ==========================================
# 🛡 OBUNANI TEKSHIRISH
# ==========================================
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"Obunani tekshirishda xatolik: {e}")
        return False

# ==========================================
# 🚀 ASOSIY BUYRUQLAR (START VA TEKSHIRISH)
# ==========================================
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear() # Har ehtimolga qarshi eski holatlarni tozalaymiz
    
    # Bazaga asinxron qo'shish
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
        await db.commit()

    if not await check_subscription(message.from_user.id):
        await message.answer(
            f"Assalomu alaykum! Botdan to'liq foydalanish uchun <b>{CHANNEL_USERNAME}</b> kanaliga a'zo bo'ling.", 
            parse_mode="HTML",
            reply_markup=get_sub_keyboard()
        )
        return

    text = (f"Xush kelibsiz, <b>{message.from_user.first_name}</b>!\n\n"
            f"Botimiz orqali mandat natijalarini, o'tish ballarini va kvotalarni bilib olishingiz mumkin.\n"
            f"Sizga shuningdek kuchli sun'iy intellekt yordamchimiz — {PARTNER_BOT} ni ham tavsiya qilamiz.\n\n"
            f"👇 Quyidagi menyudan kerakli bo'limni tanlang:")
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu)


@dp.callback_query(F.data == "check_sub")
async def check_sub_handler(callback: types.CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.delete()
        await callback.message.answer("A'zo bo'lganingiz uchun rahmat! Menyudan foydalanishingiz mumkin.", reply_markup=main_menu)
    else:
        await callback.answer("Hali kanalga a'zo bo'lmadingiz!", show_alert=True)

# ==========================================
# 📢 ADMIN PANEL (XABAR TARQATISH)
# ==========================================
@dp.message(Command("send"))
async def broadcast_message(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return 
    
    text_to_send = message.text.replace("/send", "").strip()
    
    if not text_to_send:
        return await message.answer("Iltimos, xabar matnini kiriting.\nMasalan: `/send Yangiliklar qo'shildi!`", parse_mode="Markdown")

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            users = await cursor.fetchall()
    
    count = 0
    await message.answer(f"🚀 Xabar tarqatish boshlandi... Jami baza: {len(users)} ta foydalanuvchi.")
    
    for user in users:
        try:
            await bot.send_message(chat_id=user[0], text=text_to_send)
            count += 1
            await asyncio.sleep(0.05) # Telegram API limitlaridan himoya (20 msg/sec)
        except Exception:
            pass # Bloklaganlarni e'tiborsiz qoldiradi
            
    await message.answer(f"✅ Xabar muvaffaqiyatli {count} ta foydalanuvchiga yetkazildi!")

# ==========================================
# 📊 O'TISH BALLARI
# ==========================================
@dp.message(F.text == "📊 O'tish ballari")
async def passing_scores(message: types.Message):
    await message.answer("Qaysi OTMning o'tgan yilgi o'tish ballarini ko'rmoqchisiz?\n\n*Ro'yxatdan tanlang:*", parse_mode="Markdown", reply_markup=get_otm_keyboard())

@dp.callback_query(F.data.startswith("score_"))
async def show_university_scores(callback: types.CallbackQuery):
    otm_key = callback.data.split("_")[1]
    otm_data = SCORES_DB.get(otm_key)
    
    if otm_data:
        text = f"🏫 <b>{otm_data['name']}</b>\n\n"
        for yonalish in otm_data['yonalishlar']:
            text += (f"📌 <b>{yonalish['name']}</b>\n"
                     f"🟢 Grant: {yonalish['grant']}\n"
                     f"🟠 Kontrakt: {yonalish['kontrakt']}\n\n")
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_otm_keyboard())
    await callback.answer()

# ==========================================
# 📝 ONLINE BLOK TEST (MARKETING)
# ==========================================
@dp.message(F.text == "📝 Online Blok Test")
async def online_test(message: types.Message):
    text = (
        "🔥 <b>Abituriyentlar uchun super imkoniyat!</b>\n\n"
        "O'z bilimingizni haqiqiy DTM (BMBA) standartidagi savollar bilan sinab ko'rmoqchimisiz? "
        f"Sizga maxsus <b>{TEST_BOT}</b> loyihasini tavsiya qilamiz!\n\n"
        "🌟 <b>Nimalar bor?</b>\n"
        "✅ To'liq <b>90 talik</b> (majburiy + mutaxassislik) testlar!\n"
        "✅ Har kuni qo'shiladigan <b>yangi</b> savollar bazasi.\n"
        "✅ Aniq reyting tizimi — butun respublika bilan bellashing.\n\n"
        "🚀 <i>Haqiqiy raqobatni his qilish uchun hoziroq botga o'ting!</i>"
    )
    test_bot_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Testlarni ishlash (Botga o'tish)", url=f"https://t.me/{TEST_BOT[1:]}")]
    ])
    await message.answer(text, parse_mode="HTML", reply_markup=test_bot_btn)

# ==========================================
# 🏢 KVOTALAR
# ==========================================
@dp.message(F.text == "🏢 Kvotalar")
async def quotas(message: types.Message):
    text = ("📊 <b>Qabul kvotalari (2026-yil uchun)</b>\n\n"
            "Hozirda kvotalar rasman tasdiqlanmagan. Tasdiqlanishi bilanoq barcha universitetlar kesimida shu bo'limga joylanadi.\n\n"
            "<i>Bizni kuzatishda davom eting!</i>")
    await message.answer(text, parse_mode="HTML")

# ==========================================
# 🔍 MANDAT TEKSHIRISH
# ==========================================
@dp.message(F.text == "🔍 MANDAT TEKSHIRISH (ID)")
async def mandat_start(message: types.Message, state: FSMContext):
    text = ("🆔 <b>Mandat natijasini bilish uchun Abituriyent ID raqamingizni kiriting.</b>\n\n"
            "<i>Masalan: 3145678</i>\n\n"
            "Ortga qaytish uchun menyudan istalgan boshqa tugmani bosing.")
    await message.answer(text, parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(MandatState.waiting_for_id)

@dp.message(MandatState.waiting_for_id)
async def process_mandat_id(message: types.Message, state: FSMContext):
    if message.text in ["🧮 Ball hisoblagich", "📊 O'tish ballari", "🏢 Kvotalar", "📝 Online Blok Test"]:
        await state.clear()
        await start_handler(message, state)
        return

    if message.text.isdigit() and len(message.text) >= 5:
        await message.answer(f"🔍 <b>{message.text}</b> ID raqami tahlil qilinmoqda...\n\n"
                             f"⚠️ BMBA bazasida 2026-yil javoblari hali e'lon qilinmagan. "
                             f"Avgust oyida natijangizni to'g'ridan-to'g'ri shu yerdan bilib olasiz!", 
                             parse_mode="HTML", reply_markup=main_menu)
        await state.clear()
    else:
        await message.answer("❌ Xato! ID faqat raqamlardan iborat bo'lishi va 5 ta raqamdan ko'p bo'lishi kerak. Qaytadan kiriting:")

# ==========================================
# 🧮 BALL HISOBLAGICH
# ==========================================
@dp.message(F.text == "🧮 Ball hisoblagich")
async def calc_start(message: types.Message, state: FSMContext):
    await message.answer("Majburiy fanlar blokidan (Ona tili, Tarix, Matematika) nechta savolga to'g'ri javob topdingiz? (Maks: 30)")
    await state.set_state(CalcState.majburiy)

@dp.message(CalcState.majburiy)
async def calc_majburiy(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not (0 <= int(message.text) <= 30):
        return await message.answer("⚠️ Iltimos, 0 dan 30 gacha butun son kiriting.")
    await state.update_data(majburiy=int(message.text))
    await message.answer("1-mutaxassislik fanidan to'g'ri javoblar soni? (Maks: 30)")
    await state.set_state(CalcState.mutaxassislik_1)

@dp.message(CalcState.mutaxassislik_1)
async def calc_mutaxassislik1(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not (0 <= int(message.text) <= 30):
        return await message.answer("⚠️ Iltimos, 0 dan 30 gacha butun son kiriting.")
    await state.update_data(mutaxassislik_1=int(message.text))
    await message.answer("2-mutaxassislik fanidan to'g'ri javoblar soni? (Maks: 30)")
    await state.set_state(CalcState.mutaxassislik_2)

@dp.message(CalcState.mutaxassislik_2)
async def calc_mutaxassislik2(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not (0 <= int(message.text) <= 30):
        return await message.answer("⚠️ Iltimos, 0 dan 30 gacha butun son kiriting.")
    
    data = await state.get_data()
    majburiy, mut1, mut2 = data['majburiy'], data['mutaxassislik_1'], int(message.text)
    total_score = (majburiy * 1.1) + (mut1 * 3.1) + (mut2 * 2.1)
    
    text = (f"📊 <b>Taxminiy balingiz hisoblandi:</b>\n\n"
            f"📘 Majburiy: {majburiy} ta x 1.1 = {round(majburiy * 1.1, 1)} ball\n"
            f"📙 1-mutaxassislik: {mut1} ta x 3.1 = {round(mut1 * 3.1, 1)} ball\n"
            f"📕 2-mutaxassislik: {mut2} ta x 2.1 = {round(mut2 * 2.1, 1)} ball\n\n"
            f"🏆 <b>Umumiy yig'ilgan ball: {round(total_score, 1)}</b>")
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu)
    await state.clear()

# ==========================================
# ⚙️ ISHGA TUSHIRISH
# ==========================================
async def main():
    await init_db() # Bazani ishga tushirish
    logging.basicConfig(level=logging.INFO)
    print("🚀 Mandat Bot asinxron rejimda muvaffaqiyatli ishga tushdi!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")