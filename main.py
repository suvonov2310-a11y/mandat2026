import asyncio
import logging
import aiosqlite
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.default import DefaultBotProperties

# ==========================================
# ⚙️ ASOSIY SOZLAMALAR
# ==========================================
BOT_TOKEN = "8798060376:AAH2RkSzM50-8iC6KnT_Oq8yMBws1W-ZpH0" 
ADMIN_ID = 2024143361  

CHANNEL_USERNAME = "@ozbemas_agar"
PARTNER_BOT = "@ChatAl_gptBot"
TEST_BOT = "@Abituriyent_2026Bot"
DB_NAME = "abituriyentlar.db"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# ==========================================
# 🗄 ASINXRON BAZA VA FSM HOLATLAR
# ==========================================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
        await db.commit()

class CalcState(StatesGroup):
    majburiy = State()
    mutaxassislik_1 = State()
    mutaxassislik_2 = State()

class MandatState(StatesGroup):
    waiting_for_id = State()

class SuperKontraktState(StatesGroup):
    baza_kontrakt = State()
    yetmagan_ball = State()

# ==========================================
# 📊 YIRIK OTM BAZASI (HUDUDLAR KESIMIDA)
# ==========================================
# Bu yerda har bir viloyatning asosiy OTMlari va barcha yo'nalishlari keltirilgan
REGIONS_DB = {
    "toshkent": {
        "name": "Toshkent shahri",
        "otmlar": {
            "tdiu": {"name": "Toshkent Davlat Iqtisodiyot Univ (TDIU)", "yonalishlar": [
                {"name": "Iqtisodiyot (tarmoqlar bo'yicha)", "grant": 178.5, "kontrakt": 140.2},
                {"name": "Buxgalteriya hisobi va audit", "grant": 175.0, "kontrakt": 135.5}
            ]},
            "ozmu": {"name": "O'zbekiston Milliy Universiteti (O'zMU)", "yonalishlar": [
                {"name": "Matematika", "grant": 165.2, "kontrakt": 120.4},
                {"name": "Huquqshunoslik", "grant": 182.0, "kontrakt": 150.5}
            ]}
        }
    },
    "samarqand": {
        "name": "Samarqand viloyati",
        "otmlar": {
            "samdu": {"name": "Samarqand Davlat Universiteti (SamDU)", "yonalishlar": [
                {"name": "Tarix", "grant": 155.0, "kontrakt": 110.2},
                {"name": "Psixologiya", "grant": 162.3, "kontrakt": 125.0}
            ]},
            "samtci": {"name": "Samarqand Tibbiyot Universiteti", "yonalishlar": [
                {"name": "Davolash ishi", "grant": 179.5, "kontrakt": 145.0},
                {"name": "Stomatologiya", "grant": 181.2, "kontrakt": 148.5}
            ]}
        }
    },
    "buxoro": {
        "name": "Buxoro viloyati",
        "otmlar": {
            "buxdu": {"name": "Buxoro Davlat Universiteti", "yonalishlar": [
                {"name": "Ingliz tili filologiyasi", "grant": 168.0, "kontrakt": 130.4},
                {"name": "Turizm", "grant": 150.0, "kontrakt": 105.0}
            ]}
        }
    },
    "qashqadaryo": {
        "name": "Qashqadaryo viloyati",
        "otmlar": {
            "qardu": {"name": "Qarshi Davlat Universiteti", "yonalishlar": [
                {"name": "Fizika", "grant": 145.0, "kontrakt": 100.5},
                {"name": "Boshlang'ich ta'lim", "grant": 158.5, "kontrakt": 118.0}
            ]}
        }
    },
    "fargona": {
        "name": "Farg'ona viloyati",
        "otmlar": {
            "fardu": {"name": "Farg'ona Davlat Universiteti", "yonalishlar": [
                {"name": "Komyuter ilmlari", "grant": 160.2, "kontrakt": 115.0},
                {"name": "Moliya", "grant": 165.0, "kontrakt": 122.5}
            ]}
        }
    },
    "andijon": {"name": "Andijon viloyati", "otmlar": {"adti": {"name": "Andijon Tibbiyot Instituti", "yonalishlar": [{"name": "Davolash", "grant": 175.0, "kontrakt": 140.0}]}}},
    "namangan": {"name": "Namangan viloyati", "otmlar": {"namdu": {"name": "Namangan Davlat Universiteti", "yonalishlar": [{"name": "Biologiya", "grant": 150.0, "kontrakt": 108.0}]}}},
    "xorazm": {"name": "Xorazm viloyati", "otmlar": {"urdu": {"name": "Urganch Davlat Universiteti", "yonalishlar": [{"name": "Kimyo", "grant": 148.5, "kontrakt": 105.0}]}}},
    "navoiy": {"name": "Navoiy viloyati", "otmlar": {"navdkti": {"name": "Navoiy Konchilik Instituti", "yonalishlar": [{"name": "Metallurgiya", "grant": 140.0, "kontrakt": 98.0}]}}},
    "surxondaryo": {"name": "Surxondaryo viloyati", "otmlar": {"terdu": {"name": "Termiz Davlat Universiteti", "yonalishlar": [{"name": "Geografiya", "grant": 138.0, "kontrakt": 95.0}]}}},
    "jizzax": {"name": "Jizzax viloyati", "otmlar": {"jizpi": {"name": "Jizzax Politexnika", "yonalishlar": [{"name": "Qurilish", "grant": 142.0, "kontrakt": 99.0}]}}},
    "sirdaryo": {"name": "Sirdaryo viloyati", "otmlar": {"guldu": {"name": "Guliston Davlat Universiteti", "yonalishlar": [{"name": "Pedagogika", "grant": 145.0, "kontrakt": 102.0}]}}},
    "toshkent_vil": {"name": "Toshkent viloyati", "otmlar": {"tvchdp": {"name": "Chirchiq Pedagogika Universiteti", "yonalishlar": [{"name": "Jismoniy madaniyat", "grant": 152.0, "kontrakt": 110.0}]}}},
    "qoraqalpoq": {"name": "Qoraqalpog'iston Res.", "otmlar": {"qdu": {"name": "Qoraqalpoq Davlat Univ", "yonalishlar": [{"name": "Ona tili", "grant": 140.0, "kontrakt": 95.0}]}}}
}

# ==========================================
# 🕷 AVTOMATIK YANGILIKLAR (WEB SCRAPING)
# ==========================================
LAST_NEWS_TITLE = ""

async def auto_news_parser():
    """Har 1 soatda ta'lim yangiliklarini tekshiruvchi fon (background) vazifasi."""
    global LAST_NEWS_TITLE
    await asyncio.sleep(10) # Bot to'liq ishga tushib olishi uchun kutamiz
    
    while True:
        try:
            # Ta'lim yangiliklarini olish uchun Kun.uz/talim yoki shu kabi ochiq manbadan foydalanamiz
            url = "https://kun.uz/news/category/ilm-fan"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")
                        
                        # Saytdagi eng birinchi yangilik blokini topamiz
                        news_block = soup.find("a", class_="news__title")
                        
                        if news_block:
                            title = news_block.text.strip()
                            link = "https://kun.uz" + news_block.get("href", "")
                            
                            # Agar yangilik avvalgisidan farq qilsa, hammaga tarqatamiz
                            if title and title != LAST_NEWS_TITLE:
                                LAST_NEWS_TITLE = title
                                
                                # Bazadagi barcha foydalanuvchilarni olamiz
                                async with aiosqlite.connect(DB_NAME) as db:
                                    async with db.execute("SELECT user_id FROM users") as cursor:
                                        users = await cursor.fetchall()
                                
                                text_to_send = f"🔔 <b>Ta'lim va qabuldagi yangiliklar!</b>\n\n📌 {title}\n\n👉 <a href='{link}'>Batafsil o'qish...</a>"
                                
                                for user in users:
                                    try:
                                        await bot.send_message(chat_id=user[0], text=text_to_send, disable_web_page_preview=False)
                                        await asyncio.sleep(0.05)
                                    except Exception:
                                        pass
        except Exception as e:
            logging.error(f"Parserda xatolik: {e}")
        
        # 3600 soniya (1 soat) kutamiz va yana tekshiramiz
        await asyncio.sleep(3600)

# ==========================================
# 🎛 KLAVIATURALAR
# ==========================================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="ℹ️ Qabul Yo'riqnomasi"), KeyboardButton(text="⏳ Imtihongacha vaqt")],
        [KeyboardButton(text="🧮 Ball hisoblagich"), KeyboardButton(text="💰 Super-kontrakt")],
        [KeyboardButton(text="📊 O'tish ballari"), KeyboardButton(text="📝 Online Blok Test")],
        [KeyboardButton(text="🔍 MANDAT TEKSHIRISH (ID)")]
    ],
    resize_keyboard=True
)

def get_sub_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
    ])

def get_regions_keyboard():
    """Viloyatlarni 2 ustun qilib chiqarish"""
    keys = list(REGIONS_DB.keys())
    inline_kb = []
    for i in range(0, len(keys), 2):
        row = []
        reg1 = keys[i]
        row.append(InlineKeyboardButton(text=REGIONS_DB[reg1]['name'], callback_data=f"reg_{reg1}"))
        if i + 1 < len(keys):
            reg2 = keys[i+1]
            row.append(InlineKeyboardButton(text=REGIONS_DB[reg2]['name'], callback_data=f"reg_{reg2}"))
        inline_kb.append(row)
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)

def get_otmlar_keyboard(region_id):
    """Tanlangan viloyatdagi OTMlarni chiqarish"""
    otmlar = REGIONS_DB[region_id]["otmlar"]
    inline_kb = []
    for otm_id, otm_data in otmlar.items():
        inline_kb.append([InlineKeyboardButton(text=otm_data['name'], callback_data=f"otm_{region_id}_{otm_id}")])
    inline_kb.append([InlineKeyboardButton(text="🔙 Viloyatlarga qaytish", callback_data="back_to_regions")])
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)

# ==========================================
# 🚀 ASOSIY BUYRUQLAR (START VA OBUNA)
# ==========================================
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear() 
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
        await db.commit()

    if not await check_subscription(message.from_user.id):
        return await message.answer(f"Botdan foydalanish uchun <b>{CHANNEL_USERNAME}</b> kanaliga a'zo bo'ling.", reply_markup=get_sub_keyboard())

    text = (f"Xush kelibsiz, <b>{message.from_user.first_name}</b>!\n\n"
            f"Ro'yxatdan o'tish (20-iyun) mavsumi boshlanmoqda! Bizning bot orqali barcha jarayonlarni nazorat qiling.\n"
            f"👇 Quyidagi menyudan kerakli bo'limni tanlang:")
    await message.answer(text, reply_markup=main_menu)

@dp.callback_query(F.data == "check_sub")
async def check_sub_handler(callback: types.CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.delete()
        await callback.message.answer("A'zo bo'lganingiz uchun rahmat!", reply_markup=main_menu)
    else:
        await callback.answer("Hali kanalga a'zo bo'lmadingiz!", show_alert=True)

# ==========================================
# 📊 O'TISH BALLARI (AQLI TIZIM)
# ==========================================
@dp.message(F.text == "📊 O'tish ballari")
async def passing_scores(message: types.Message):
    await message.answer("📍 <b>Qaysi hududdagi</b> OTMlarni ko'rmoqchisiz? Ro'yxatdan tanlang:", reply_markup=get_regions_keyboard())

@dp.callback_query(F.data.startswith("reg_"))
async def show_otms_in_region(callback: types.CallbackQuery):
    region_id = callback.data.split("_")[1]
    reg_name = REGIONS_DB[region_id]["name"]
    await callback.message.edit_text(f"🏫 <b>{reg_name}</b> bo'yicha OTMlar:\nKerakli universitetni tanlang:", reply_markup=get_otmlar_keyboard(region_id))

@dp.callback_query(F.data == "back_to_regions")
async def back_to_regions(callback: types.CallbackQuery):
    await callback.message.edit_text("📍 <b>Qaysi hududdagi</b> OTMlarni ko'rmoqchisiz? Ro'yxatdan tanlang:", reply_markup=get_regions_keyboard())

@dp.callback_query(F.data.startswith("otm_"))
async def show_university_scores(callback: types.CallbackQuery):
    _, region_id, otm_id = callback.data.split("_")
    otm_data = REGIONS_DB[region_id]["otmlar"][otm_id]
    
    text = f"🏫 <b>{otm_data['name']}</b> o'tish ballari:\n\n"
    for yonalish in otm_data['yonalishlar']:
        text += (f"📌 <b>{yonalish['name']}</b>\n"
                 f"🟢 Grant: {yonalish['grant']} ball\n"
                 f"🟠 Kontrakt: {yonalish['kontrakt']} ball\n\n")
                 
    await callback.message.edit_text(text, reply_markup=get_otmlar_keyboard(region_id))

# ==========================================
# 💰 SUPER-KONTRAKT KALKULYATORI
# ==========================================
@dp.message(F.text == "💰 Super-kontrakt")
async def super_contract_start(message: types.Message, state: FSMContext):
    await message.answer("💰 <b>Super-kontrakt hisoblash:</b>\n\nOTMning yillik bazaviy to'lov-kontrakt summasini kiriting (Masalan, 9000000 yoki 12000000):")
    await state.set_state(SuperKontraktState.baza_kontrakt)

@dp.message(SuperKontraktState.baza_kontrakt)
async def super_contract_base(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("⚠️ Iltimos, faqat raqamlar bilan kiriting.")
    await state.update_data(baza_kontrakt=int(message.text))
    await message.answer("O'tish baliga (chiziqqa) necha ball yetmay qoldi? (Masalan: 0.5 yoki 2.3):")
    await state.set_state(SuperKontraktState.yetmagan_ball)

@dp.message(SuperKontraktState.yetmagan_ball)
async def super_contract_calc(message: types.Message, state: FSMContext):
    try:
        yetmagan = float(message.text)
    except ValueError:
        return await message.answer("⚠️ Iltimos, to'g'ri son kiriting (masalan: 1.5).")
    
    data = await state.get_data()
    baza = data['baza_kontrakt']
    
    if yetmagan <= 1.05: barobar = 1.5
    elif yetmagan <= 2.10: barobar = 2.0
    elif yetmagan <= 3.15: barobar = 2.5
    elif yetmagan <= 4.20: barobar = 3.0
    else: barobar = 10 
    
    jami_summa = baza * barobar
    text = (f"📊 <b>Super-kontrakt hisob-kitobi:</b>\n\n"
            f"➖ Yetmagan ball: <b>{yetmagan}</b>\n"
            f"✖️ Ko'paytma: <b>{barobar} barobar</b>\n\n"
            f"💳 <b>To'lanishi kerak bo'lgan summa:</b>\n"
            f"💲 {jami_summa:,.0f} so'm")
    if barobar == 10:
        text += "\n\n<i>⚠️ 4.20 balldan ko'p yetmasa, OTM o'zi hal qiladi (min 10 barobar).</i>"
        
    await message.answer(text, reply_markup=main_menu)
    await state.clear()

# ==========================================
# 🧮 BALL HISOBLAGICH VA BOSHQA BO'LIMLAR
# ==========================================
@dp.message(F.text == "ℹ️ Qabul Yo'riqnomasi")
async def admission_guide(message: types.Message):
    text = ("🎓 <b>2026 Qabul Yo'riqnomasi</b>\n\n"
            "Abituriyentlar 20-iyundan 20-iyulga qadar <b>my.uzbmb.uz</b> portali orqali onlayn ro'yxatdan o'tadilar.\n"
            "Bu yil avval test topshirasiz, ballingiz chiqqach, OTMlarni tanlaysiz (Adashish xavfi past)!")
    btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🌐 My.uzbmb.uz saytiga o'tish", url="https://my.uzbmb.uz")]])
    await message.answer(text, reply_markup=btn)

@dp.message(F.text == "⏳ Imtihongacha vaqt")
async def countdown_to_exam(message: types.Message):
    today = datetime.now()
    exam_date = datetime(2026, 7, 25) 
    if today > exam_date:
        await message.answer("Imtihonlar boshlangan! Mandatni kuting.")
    else:
        delta = exam_date - today
        await message.answer(f"⏳ <b>Asosiy Imtihonlargacha qolgan vaqt:</b>\n\n🗓 Kun: <b>{delta.days}</b>\n⏰ Soat: <b>{delta.seconds // 3600}</b>")

@dp.message(F.text == "📝 Online Blok Test")
async def online_test(message: types.Message):
    text = (f"🔥 Haqiqiy DTM savollari bilan bellashing!\nSizga maxsus <b>{TEST_BOT}</b> ni tavsiya qilamiz!")
    btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🚀 Testlarni ishlash", url=f"https://t.me/{TEST_BOT[1:]}")]])
    await message.answer(text, reply_markup=btn)

@dp.message(F.text == "🏢 Kvotalar")
async def quotas(message: types.Message):
    await message.answer("📊 <b>Qabul kvotalari</b>\nHozirda tasdiqlanmagan. Tez kunda joylanadi.")

@dp.message(F.text == "🔍 MANDAT TEKSHIRISH (ID)")
async def mandat_start(message: types.Message, state: FSMContext):
    await message.answer("🆔 <b>Abituriyent ID raqamingizni kiriting:</b>", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(MandatState.waiting_for_id)

@dp.message(MandatState.waiting_for_id)
async def process_mandat_id(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await state.clear()
        return await start_handler(message, state)
    await message.answer(f"🔍 <b>{message.text}</b> ID tekshirilmoqda...\n⚠️ BMBA (Mandat) bazasi avgust oyida ochiladi!", reply_markup=main_menu)
    await state.clear()

@dp.message(F.text == "🧮 Ball hisoblagich")
async def calc_start(message: types.Message, state: FSMContext):
    await message.answer("Majburiy fanlar (Ona tili, Tarix, Matematika) to'g'ri javoblari soni? (Maks: 30)")
    await state.set_state(CalcState.majburiy)

@dp.message(CalcState.majburiy)
async def calc_majburiy(message: types.Message, state: FSMContext):
    await state.update_data(majburiy=int(message.text))
    await message.answer("1-mutaxassislik to'g'ri javoblari soni? (Maks: 30)")
    await state.set_state(CalcState.mutaxassislik_1)

@dp.message(CalcState.mutaxassislik_1)
async def calc_mutaxassislik1(message: types.Message, state: FSMContext):
    await state.update_data(mutaxassislik_1=int(message.text))
    await message.answer("2-mutaxassislik to'g'ri javoblari soni? (Maks: 30)")
    await state.set_state(CalcState.mutaxassislik_2)

@dp.message(CalcState.mutaxassislik_2)
async def calc_mutaxassislik2(message: types.Message, state: FSMContext):
    data = await state.get_data()
    m, m1, m2 = data['majburiy'], data['mutaxassislik_1'], int(message.text)
    total = (m * 1.1) + (m1 * 3.1) + (m2 * 2.1)
    await message.answer(f"📊 <b>Umumiy yig'ilgan ball: {round(total, 1)}</b>", reply_markup=main_menu)
    await state.clear()

# ==========================================
# ⚙️ ISHGA TUSHIRISH (ASOSIY TSIKL)
# ==========================================
async def main():
    await init_db() 
    logging.basicConfig(level=logging.INFO)
    print("🚀 Mandat Bot (Parser + 14 Viloyat) muvaffaqiyatli ishga tushdi!")
    
    # Parser funksiyasini orqa fonda ishga tushiramiz
    asyncio.create_task(auto_news_parser())
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")