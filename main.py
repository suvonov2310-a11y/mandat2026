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

class ChanceState(StatesGroup):
    waiting_for_score = State()

class BroadcastState(StatesGroup):
    waiting_for_post = State()

# ==========================================
# 📊 YIRIK OTM BAZASI (QOLGANINI O'ZINGIZ TO'LDIRASIZ)
# ==========================================
REGIONS_DB = {
    "toshkent": {
        "name": "Toshkent shahri",
        "otmlar": {
            "ozmu": {"name": "O'zbekiston Milliy Universiteti", "yonalishlar": [
                {"name": "Matematika", "grant": 165.2, "kontrakt": 120.4},
                {"name": "Fizika", "grant": 158.0, "kontrakt": 115.0},
                {"name": "Tarix", "grant": 155.0, "kontrakt": 110.0},
                {"name": "Psixologiya", "grant": 168.0, "kontrakt": 125.0},
                {"name": "Biologiya", "grant": 160.0, "kontrakt": 118.0}
            ]},
            "tdtu": {"name": "Toshkent Davlat Texnika Universiteti", "yonalishlar": [
                {"name": "Elektr energetikasi", "grant": 155.0, "kontrakt": 110.0},
                {"name": "Mashinasozlik", "grant": 145.0, "kontrakt": 105.0},
                {"name": "Mexatronika va robototexnika", "grant": 160.0, "kontrakt": 115.0}
            ]},
            "tdiu": {"name": "Toshkent Davlat Iqtisodiyot Univ.", "yonalishlar": [
                {"name": "Iqtisodiyot (tarmoqlar)", "grant": 178.5, "kontrakt": 140.2},
                {"name": "Buxgalteriya hisobi", "grant": 175.0, "kontrakt": 135.5},
                {"name": "Moliya", "grant": 180.2, "kontrakt": 145.0}
            ]},
            "tmi": {"name": "Toshkent Moliya Instituti", "yonalishlar": [
                {"name": "Soliq va soliqqa tortish", "grant": 170.0, "kontrakt": 132.0},
                {"name": "Bank ishi va audit", "grant": 175.0, "kontrakt": 138.0}
            ]},
            "tdyu": {"name": "Toshkent Davlat Yuridik Univ.", "yonalishlar": [
                {"name": "Xalqaro huquq", "grant": 182.5, "kontrakt": 155.0},
                {"name": "Jinoiy huquq", "grant": 184.0, "kontrakt": 158.2},
                {"name": "Biznes huquqi", "grant": 180.5, "kontrakt": 152.0}
            ]},
            "tatu": {"name": "Toshkent Axborot Texnologiyalari Univ.", "yonalishlar": [
                {"name": "Dasturiy injiniring", "grant": 180.5, "kontrakt": 148.0},
                {"name": "Kiberxavfsizlik", "grant": 176.2, "kontrakt": 142.5},
                {"name": "Sun'iy intellekt", "grant": 185.0, "kontrakt": 150.0}
            ]},
            "tta": {"name": "Toshkent Tibbiyot Akademiyasi", "yonalishlar": [
                {"name": "Davolash ishi", "grant": 180.0, "kontrakt": 145.0},
                {"name": "Tibbiy profilaktika", "grant": 165.0, "kontrakt": 130.0}
            ]},
            "tashpmi": {"name": "Toshkent Pediatriya Tibbiyot Instituti", "yonalishlar": [
                {"name": "Pediatriya ishi", "grant": 175.0, "kontrakt": 138.0},
                {"name": "Tibbiy biologiya", "grant": 160.0, "kontrakt": 125.0}
            ]},
            "tdpu": {"name": "Toshkent Davlat Pedagogika Univ.", "yonalishlar": [
                {"name": "Boshlang'ich ta'lim", "grant": 165.0, "kontrakt": 120.0},
                {"name": "Maktabgacha ta'lim", "grant": 155.0, "kontrakt": 110.0},
                {"name": "Ona tili va adabiyot", "grant": 160.0, "kontrakt": 115.0}
            ]},
            "ozdjtu": {"name": "O'zbekiston Davlat Jahon Tillari Univ.", "yonalishlar": [
                {"name": "Ingliz tili filologiyasi", "grant": 172.0, "kontrakt": 135.0},
                {"name": "Tarjimonlik (Ingliz tili)", "grant": 175.0, "kontrakt": 138.0},
                {"name": "Xalqaro jurnalistika", "grant": 168.0, "kontrakt": 130.0}
            ]},
            "tdshu": {"name": "Toshkent Davlat Sharqshunoslik Univ.", "yonalishlar": [
                {"name": "Koreys tili", "grant": 170.0, "kontrakt": 135.0},
                {"name": "Arab tili", "grant": 165.0, "kontrakt": 125.0},
                {"name": "Sharq falsafasi va tarixi", "grant": 155.0, "kontrakt": 110.0}
            ]},
            "jidu": {"name": "Jahon Iqtisodiyoti va Diplomatiya Univ.", "yonalishlar": [
                {"name": "Xalqaro munosabatlar", "grant": 185.0, "kontrakt": 155.0},
                {"name": "Xalqaro huquq", "grant": 182.0, "kontrakt": 152.0}
            ]},
            "tdtu_trans": {"name": "Toshkent Davlat Transport Univ.", "yonalishlar": [
                {"name": "Logistika (transport)", "grant": 160.0, "kontrakt": 115.0},
                {"name": "Avtomobil transporti", "grant": 150.0, "kontrakt": 105.0}
            ]},
            "taqu": {"name": "Toshkent Arxitektura-Qurilish Univ.", "yonalishlar": [
                {"name": "Arxitektura", "grant": 165.0, "kontrakt": 120.0},
                {"name": "Qurilish", "grant": 150.0, "kontrakt": 108.0}
            ]},
            "ttesi": {"name": "Toshkent To'qimachilik Sanoati Inst.", "yonalishlar": [
                {"name": "To'qimachilik injiniringi", "grant": 140.0, "kontrakt": 98.0},
                {"name": "Kiyim dizayni", "grant": 145.0, "kontrakt": 105.0}
            ]},
            "tkti": {"name": "Toshkent Kimyo-Texnologiya Instituti", "yonalishlar": [
                {"name": "Oziq-ovqat texnologiyasi", "grant": 148.0, "kontrakt": 105.0},
                {"name": "Kimyoviy texnologiya", "grant": 145.0, "kontrakt": 102.0}
            ]},
            "ozdsmi": {"name": "O'zbekiston San'at va Madaniyat Inst.", "yonalishlar": [
                {"name": "Aktyorlik san'ati", "grant": 155.0, "kontrakt": 110.0},
                {"name": "Rejissyorlik", "grant": 160.0, "kontrakt": 115.0}
            ]}
        }
    },
    "samarqand": {
        "name": "Samarqand viloyati",
        "otmlar": {
            "samdu": {"name": "Samarqand Davlat Universiteti", "yonalishlar": [
                {"name": "Tarix", "grant": 155.0, "kontrakt": 110.0},
                {"name": "Psixologiya", "grant": 162.0, "kontrakt": 125.0},
                {"name": "Matematika", "grant": 152.0, "kontrakt": 112.0}
            ]},
            "samtci": {"name": "Samarqand Tibbiyot Universiteti", "yonalishlar": [
                {"name": "Davolash ishi", "grant": 179.5, "kontrakt": 145.0},
                {"name": "Stomatologiya", "grant": 181.2, "kontrakt": 148.5}
            ]},
            "samdchti": {"name": "Samarqand Chet Tillari Instituti", "yonalishlar": [
                {"name": "Ingliz tili", "grant": 170.0, "kontrakt": 135.0},
                {"name": "Yapon tili", "grant": 165.0, "kontrakt": 125.0}
            ]},
            "samisi": {"name": "Samarqand Iqtisodiyot va Servis Inst.", "yonalishlar": [
                {"name": "Moliya", "grant": 160.0, "kontrakt": 120.0},
                {"name": "Turizm", "grant": 150.0, "kontrakt": 105.0}
            ]},
            "samdaqu": {"name": "Samarqand Arxitektura-Qurilish Univ.", "yonalishlar": [
                {"name": "Arxitektura", "grant": 155.0, "kontrakt": 115.0},
                {"name": "Bino va inshootlar qurilishi", "grant": 148.0, "kontrakt": 105.0}
            ]},
            "ipak_yoli": {"name": "Ipak Yo'li Turizm Xalqaro Univ.", "yonalishlar": [
                {"name": "Turizm (Xalqaro)", "grant": 165.0, "kontrakt": 125.0},
                {"name": "Gid hamrohligi", "grant": 155.0, "kontrakt": 115.0}
            ]},
            "samvmi": {"name": "Samarqand Veterinariya Meditsinasi Inst.", "yonalishlar": [
                {"name": "Veterinariya", "grant": 145.0, "kontrakt": 100.0},
                {"name": "Chorvachilik", "grant": 138.0, "kontrakt": 95.0}
            ]}
        }
    },
    "buxoro": {
        "name": "Buxoro viloyati",
        "otmlar": {
            "buxdu": {"name": "Buxoro Davlat Universiteti", "yonalishlar": [
                {"name": "Ingliz tili", "grant": 168.0, "kontrakt": 130.0},
                {"name": "Tarix", "grant": 148.0, "kontrakt": 102.0}
            ]},
            "buxti": {"name": "Buxoro Tibbiyot Instituti", "yonalishlar": [
                {"name": "Davolash ishi", "grant": 172.0, "kontrakt": 138.0},
                {"name": "Stomatologiya", "grant": 175.5, "kontrakt": 142.0}
            ]},
            "buxmti": {"name": "Buxoro Muhandislik Texnologiyalari Inst.", "yonalishlar": [
                {"name": "Neft va gaz ishi", "grant": 155.0, "kontrakt": 115.0},
                {"name": "Energetika", "grant": 145.0, "kontrakt": 105.0}
            ]},
            "buxdpi": {"name": "Buxoro Davlat Pedagogika Instituti", "yonalishlar": [
                {"name": "Boshlang'ich ta'lim", "grant": 158.0, "kontrakt": 112.0},
                {"name": "Matematika o'qitish", "grant": 150.0, "kontrakt": 105.0}
            ]},
            "tiiame_bux": {"name": "TQXMI Buxoro filiali", "yonalishlar": [
                {"name": "Suv xo'jaligi", "grant": 140.0, "kontrakt": 95.0}
            ]}
        }
    },
    "qashqadaryo": {
        "name": "Qashqadaryo viloyati",
        "otmlar": {
            "qardu": {"name": "Qarshi Davlat Universiteti", "yonalishlar": [
                {"name": "Fizika", "grant": 145.0, "kontrakt": 100.0},
                {"name": "Kimyo", "grant": 148.0, "kontrakt": 102.0}
            ]},
            "qmii": {"name": "Qarshi Muhandislik-Iqtisodiyot Inst.", "yonalishlar": [
                {"name": "Iqtisodiyot", "grant": 160.0, "kontrakt": 115.0},
                {"name": "Neft-gaz ishi", "grant": 165.0, "kontrakt": 120.0}
            ]},
            "shahdpi": {"name": "Shahrisabz Davlat Pedagogika Inst.", "yonalishlar": [
                {"name": "Ona tili va adabiyot", "grant": 142.0, "kontrakt": 98.0},
                {"name": "Ingliz tili", "grant": 155.0, "kontrakt": 110.0}
            ]},
            "tatu_qar": {"name": "TATU Qarshi filiali", "yonalishlar": [
                {"name": "Dasturiy injiniring", "grant": 158.0, "kontrakt": 115.0},
                {"name": "Kiberxavfsizlik", "grant": 152.0, "kontrakt": 110.0}
            ]},
            "tta_qar": {"name": "TTA Qarshi filiali", "yonalishlar": [
                {"name": "Davolash ishi", "grant": 172.0, "kontrakt": 135.0}
            ]},
            "tiiame_qar": {"name": "TQXMI Qarshi filiali", "yonalishlar": [
                {"name": "Gidrotexnika", "grant": 138.0, "kontrakt": 95.0}
            ]}
        }
    },
    "fargona": {
        "name": "Farg'ona viloyati",
        "otmlar": {
            "fardu": {"name": "Farg'ona Davlat Universiteti", "yonalishlar": [
                {"name": "Komyuter ilmlari", "grant": 160.0, "kontrakt": 115.0},
                {"name": "Moliya", "grant": 165.0, "kontrakt": 122.0}
            ]},
            "farpi": {"name": "Farg'ona Politexnika Instituti", "yonalishlar": [
                {"name": "Energetika", "grant": 150.0, "kontrakt": 108.0},
                {"name": "Mexatronika", "grant": 155.0, "kontrakt": 112.0}
            ]},
            "ttafar": {"name": "TTA Farg'ona filiali", "yonalishlar": [
                {"name": "Davolash ishi", "grant": 170.0, "kontrakt": 135.0}
            ]},
            "far_js_ti": {"name": "Farg'ona Jamoat Salomatligi Tibbiyot Inst.", "yonalishlar": [
                {"name": "Profilaktika ishi", "grant": 165.0, "kontrakt": 128.0},
                {"name": "Farmatsiya", "grant": 160.0, "kontrakt": 125.0}
            ]},
            "tatu_far": {"name": "TATU Farg'ona filiali", "yonalishlar": [
                {"name": "Axborot xavfsizligi", "grant": 162.0, "kontrakt": 118.0}
            ]},
            "ozdsmi_far": {"name": "San'at va Madaniyat Inst. Farg'ona", "yonalishlar": [
                {"name": "Vokal san'ati", "grant": 145.0, "kontrakt": 100.0}
            ]}
        }
    },
    "andijon": {
        "name": "Andijon viloyati",
        "otmlar": {
            "adti": {"name": "Andijon Tibbiyot Instituti", "yonalishlar": [
                {"name": "Davolash ishi", "grant": 175.0, "kontrakt": 140.0},
                {"name": "Pediatriya", "grant": 170.0, "kontrakt": 135.0}
            ]},
            "adu": {"name": "Andijon Davlat Universiteti", "yonalishlar": [
                {"name": "Biologiya", "grant": 150.0, "kontrakt": 105.0},
                {"name": "Boshlang'ich ta'lim", "grant": 155.0, "kontrakt": 112.0}
            ]},
            "andmi": {"name": "Andijon Mashinasozlik Instituti", "yonalishlar": [
                {"name": "Avtomobilsozlik", "grant": 145.0, "kontrakt": 102.0},
                {"name": "Mashinasozlik", "grant": 140.0, "kontrakt": 98.0}
            ]},
            "adpi": {"name": "Andijon Davlat Pedagogika Instituti", "yonalishlar": [
                {"name": "Jismoniy madaniyat", "grant": 148.0, "kontrakt": 105.0},
                {"name": "Informatika o'qitish", "grant": 142.0, "kontrakt": 98.0}
            ]},
            "and_agrox": {"name": "Andijon Qishloq Xo'jaligi Inst.", "yonalishlar": [
                {"name": "Agronomiya", "grant": 135.0, "kontrakt": 90.0}
            ]}
        }
    },
    "namangan": {
        "name": "Namangan viloyati",
        "otmlar": {
            "namdu": {"name": "Namangan Davlat Universiteti", "yonalishlar": [
                {"name": "Matematika", "grant": 148.0, "kontrakt": 105.0},
                {"name": "Ingliz tili", "grant": 162.0, "kontrakt": 120.0}
            ]},
            "nammqi": {"name": "Namangan Muhandislik-Qurilish Inst.", "yonalishlar": [
                {"name": "Qurilish", "grant": 140.0, "kontrakt": 98.0},
                {"name": "Arxitektura", "grant": 150.0, "kontrakt": 110.0}
            ]},
            "namti": {"name": "Namangan To'qimachilik Sanoati Inst.", "yonalishlar": [
                {"name": "To'qimachilik dizayni", "grant": 135.0, "kontrakt": 95.0}
            ]},
            "namdpi": {"name": "Namangan Davlat Pedagogika Instituti", "yonalishlar": [
                {"name": "Boshlang'ich ta'lim", "grant": 155.0, "kontrakt": 110.0}
            ]},
            "namdchti": {"name": "Namangan Davlat Chet Tillari Inst.", "yonalishlar": [
                {"name": "Koreys tili", "grant": 160.0, "kontrakt": 115.0}
            ]}
        }
    },
    "xorazm": {
        "name": "Xorazm viloyati",
        "otmlar": {
            "urdu": {"name": "Urganch Davlat Universiteti", "yonalishlar": [
                {"name": "Kimyo", "grant": 148.0, "kontrakt": 105.0},
                {"name": "Fizika", "grant": 145.0, "kontrakt": 100.0}
            ]},
            "ttaur": {"name": "TTA Urganch filiali", "yonalishlar": [
                {"name": "Davolash ishi", "grant": 168.0, "kontrakt": 132.0},
                {"name": "Pediatriya ishi", "grant": 162.0, "kontrakt": 128.0}
            ]},
            "tatu_ur": {"name": "TATU Urganch filiali", "yonalishlar": [
                {"name": "Dasturiy injiniring", "grant": 155.0, "kontrakt": 112.0}
            ]},
            "urdpi": {"name": "Urganch Davlat Pedagogika Instituti", "yonalishlar": [
                {"name": "Matematika", "grant": 145.0, "kontrakt": 102.0}
            ]},
            "ur_ranch": {"name": "Urganch Ranch Texnologiya Univ.", "yonalishlar": [
                {"name": "Axborot tizimlari", "grant": 140.0, "kontrakt": 98.0}
            ]}
        }
    },
    "navoiy": {
        "name": "Navoiy viloyati",
        "otmlar": {
            "ndki": {"name": "Navoiy Davlat Konchilik Univ.", "yonalishlar": [
                {"name": "Metallurgiya", "grant": 140.0, "kontrakt": 98.0},
                {"name": "Konchilik ishi", "grant": 145.0, "kontrakt": 102.0}
            ]},
            "navdpi": {"name": "Navoiy Davlat Pedagogika Instituti", "yonalishlar": [
                {"name": "Matematika", "grant": 148.0, "kontrakt": 105.0},
                {"name": "Tarix", "grant": 142.0, "kontrakt": 98.0}
            ]}
        }
    },
    "surxondaryo": {
        "name": "Surxondaryo viloyati",
        "otmlar": {
            "terdu": {"name": "Termiz Davlat Universiteti", "yonalishlar": [
                {"name": "Geografiya", "grant": 138.0, "kontrakt": 95.0},
                {"name": "O'zbek tili", "grant": 142.0, "kontrakt": 98.0}
            ]},
            "terpi": {"name": "Termiz Davlat Pedagogika Instituti", "yonalishlar": [
                {"name": "Ingliz tili", "grant": 155.0, "kontrakt": 115.0},
                {"name": "Boshlang'ich ta'lim", "grant": 148.0, "kontrakt": 105.0}
            ]},
            "ter_muh": {"name": "Termiz Muhandislik-Texnologiya Inst.", "yonalishlar": [
                {"name": "Yengil sanoat", "grant": 135.0, "kontrakt": 92.0}
            ]},
            "ter_agro": {"name": "Termiz Agrotexnologiyalar Inst.", "yonalishlar": [
                {"name": "Agronomiya", "grant": 130.0, "kontrakt": 88.0}
            ]},
            "tta_ter": {"name": "TTA Termiz filiali", "yonalishlar": [
                {"name": "Davolash ishi", "grant": 165.0, "kontrakt": 130.0}
            ]}
        }
    },
    "jizzax": {
        "name": "Jizzax viloyati",
        "otmlar": {
            "jizpi": {"name": "Jizzax Politexnika Instituti", "yonalishlar": [
                {"name": "Qurilish", "grant": 142.0, "kontrakt": 99.0},
                {"name": "Elektr texnikasi", "grant": 145.0, "kontrakt": 102.0}
            ]},
            "jdu": {"name": "Jizzax Davlat Universiteti", "yonalishlar": [
                {"name": "Biologiya", "grant": 140.0, "kontrakt": 95.0},
                {"name": "Fizika", "grant": 138.0, "kontrakt": 92.0}
            ]},
            "jdpu": {"name": "Jizzax Davlat Pedagogika Universiteti", "yonalishlar": [
                {"name": "Ingliz tili", "grant": 152.0, "kontrakt": 110.0},
                {"name": "Boshlang'ich ta'lim", "grant": 148.0, "kontrakt": 105.0}
            ]},
            "qazan_jiz": {"name": "Qozon Federal Univ. Jizzax filiali", "yonalishlar": [
                {"name": "Kiberxavfsizlik", "grant": 155.0, "kontrakt": 115.0}
            ]}
        }
    },
    "sirdaryo": {
        "name": "Sirdaryo viloyati",
        "otmlar": {
            "guldu": {"name": "Guliston Davlat Universiteti", "yonalishlar": [
                {"name": "Pedagogika", "grant": 145.0, "kontrakt": 102.0},
                {"name": "Agronomiya", "grant": 135.0, "kontrakt": 90.0}
            ]},
            "sir_dpi": {"name": "Sirdaryo Pedagogika Instituti", "yonalishlar": [
                {"name": "Boshlang'ich ta'lim", "grant": 140.0, "kontrakt": 95.0}
            ]},
            "tkti_yan": {"name": "TKTI Yangiyer filiali", "yonalishlar": [
                {"name": "Kimyo texnologiya", "grant": 138.0, "kontrakt": 95.0}
            ]}
        }
    },
    "toshkent_vil": {
        "name": "Toshkent viloyati",
        "otmlar": {
            "tvchdp": {"name": "Chirchiq Pedagogika Universiteti", "yonalishlar": [
                {"name": "Jismoniy madaniyat", "grant": 152.0, "kontrakt": 110.0},
                {"name": "Tarix", "grant": 148.0, "kontrakt": 105.0}
            ]},
            "tdau": {"name": "Toshkent Davlat Agrar Universiteti", "yonalishlar": [
                {"name": "Qishloq xo'jaligi iqtisodiyoti", "grant": 145.0, "kontrakt": 102.0},
                {"name": "Agrokimyo", "grant": 135.0, "kontrakt": 90.0}
            ]},
            "tdtu_olm": {"name": "TDTU Olmaliq filiali", "yonalishlar": [
                {"name": "Metallurgiya", "grant": 140.0, "kontrakt": 95.0},
                {"name": "Konchilik", "grant": 138.0, "kontrakt": 92.0}
            ]},
            "ozdsjtsu": {"name": "O'zbekiston Jismoniy Tarbiya Univ.", "yonalishlar": [
                {"name": "Sport faoliyati (Boks)", "grant": 145.0, "kontrakt": 100.0},
                {"name": "Futbol", "grant": 150.0, "kontrakt": 105.0}
            ]}
        }
    },
    "qoraqalpoq": {
        "name": "Qoraqalpog'iston Res.",
        "otmlar": {
            "qdu": {"name": "Qoraqalpoq Davlat Universiteti", "yonalishlar": [
                {"name": "Ona tili", "grant": 140.0, "kontrakt": 95.0},
                {"name": "Yurisprudensiya", "grant": 170.0, "kontrakt": 135.0}
            ]},
            "nukpi": {"name": "Nukus Pedagogika Instituti", "yonalishlar": [
                {"name": "Boshlang'ich ta'lim", "grant": 145.0, "kontrakt": 100.0},
                {"name": "Informatika", "grant": 138.0, "kontrakt": 95.0}
            ]},
            "tatunuk": {"name": "TATU Nukus filiali", "yonalishlar": [
                {"name": "Dasturiy injiniring", "grant": 150.0, "kontrakt": 110.0}
            ]},
            "tta_nuk": {"name": "TTA Nukus filiali", "yonalishlar": [
                {"name": "Davolash ishi", "grant": 165.0, "kontrakt": 130.0}
            ]},
            "qor_med": {"name": "Qoraqalpoq Tibbiyot Instituti", "yonalishlar": [
                {"name": "Pediatriya ishi", "grant": 160.0, "kontrakt": 125.0}
            ]},
            "qor_qxi": {"name": "Qoraqalpoq Qishloq Xo'jaligi Inst.", "yonalishlar": [
                {"name": "Agronomiya", "grant": 130.0, "kontrakt": 88.0}
            ]},
            "ndki_nuk": {"name": "NDKI Nukus filiali", "yonalishlar": [
                {"name": "Konchilik", "grant": 135.0, "kontrakt": 92.0}
            ]}
        }
    }
}

# ==========================================
# 🕷 AVTOMATIK YANGILIKLAR PARSERI
# ==========================================
LAST_NEWS_TITLE = ""

async def auto_news_parser():
    global LAST_NEWS_TITLE
    await asyncio.sleep(15) 
    
    while True:
        try:
            url = "https://kun.uz/news/category/ilm-fan"
            headers = {"User-Agent": "Mozilla/5.0"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")
                        news_block = soup.find("a", class_="news__title")
                        
                        if news_block:
                            title = news_block.text.strip()
                            link = "https://kun.uz" + news_block.get("href", "")
                            
                            if title and title != LAST_NEWS_TITLE:
                                LAST_NEWS_TITLE = title
                                async with aiosqlite.connect(DB_NAME) as db:
                                    async with db.execute("SELECT user_id FROM users") as cursor:
                                        users = await cursor.fetchall()
                                
                                text = f"🔔 <b>Qabul va Ta'lim yangiliklari!</b>\n\n📌 {title}\n\n👉 <a href='{link}'>Batafsil o'qish...</a>"
                                for user in users:
                                    try:
                                        await bot.send_message(chat_id=user[0], text=text, disable_web_page_preview=False)
                                        await asyncio.sleep(0.05)
                                    except Exception:
                                        pass
        except Exception as e:
            logging.error(f"Parser xatosi: {e}")
        
        await asyncio.sleep(3600)

# ==========================================
# 🎛 KLAVIATURALAR VA MENYULAR
# ==========================================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="ℹ️ Qabul Yo'riqnomasi"), KeyboardButton(text="⏳ Imtihongacha vaqt")],
        [KeyboardButton(text="🧮 Ball hisoblagich"), KeyboardButton(text="💰 Super-kontrakt")],
        [KeyboardButton(text="📊 O'tish ballari"), KeyboardButton(text="🎯 Imkoniyatni baholash")],
        [KeyboardButton(text="🏢 Kvotalar"), KeyboardButton(text="📝 Online Blok Test")],
        [KeyboardButton(text="🔍 MANDAT TEKSHIRISH (ID)")]
    ],
    resize_keyboard=True
)

def get_sub_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
    ])

def get_regions_keyboard(prefix="reg"):
    keys = list(REGIONS_DB.keys())
    inline_kb = []
    for i in range(0, len(keys), 2):
        row = []
        reg1 = keys[i]
        row.append(InlineKeyboardButton(text=REGIONS_DB[reg1]['name'], callback_data=f"{prefix}_{reg1}"))
        if i + 1 < len(keys):
            reg2 = keys[i+1]
            row.append(InlineKeyboardButton(text=REGIONS_DB[reg2]['name'], callback_data=f"{prefix}_{reg2}"))
        inline_kb.append(row)
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)

def get_otmlar_keyboard(region_id, prefix="otm"):
    otmlar = REGIONS_DB.get(region_id, {}).get("otmlar", {})
    inline_kb = []
    for otm_id, otm_data in otmlar.items():
        inline_kb.append([InlineKeyboardButton(text=otm_data['name'], callback_data=f"{prefix}_{region_id}_{otm_id}")])
    back_data = "back_to_regions" if prefix == "otm" else "chance_back_to_regions"
    inline_kb.append([InlineKeyboardButton(text="🔙 Viloyatlarga qaytish", callback_data=back_data)])
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)

def get_yonalishlar_keyboard(region_id, otm_id):
    yonalishlar = REGIONS_DB[region_id]["otmlar"][otm_id]["yonalishlar"]
    inline_kb = []
    for idx, yon in enumerate(yonalishlar):
        inline_kb.append([InlineKeyboardButton(text=yon['name'], callback_data=f"chyon_{region_id}_{otm_id}_{idx}")])
    inline_kb.append([InlineKeyboardButton(text="🔙 OTMlarga qaytish", callback_data=f"chance_reg_{region_id}")])
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
    
    # Foydalanuvchini bazaga qo'shish
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
        await db.commit()

    if not await check_subscription(message.from_user.id):
        return await message.answer(f"Botdan foydalanish uchun <b>{CHANNEL_USERNAME}</b> kanaliga a'zo bo'ling.", reply_markup=get_sub_keyboard())

    text = (f"Xush kelibsiz, <b>{message.from_user.first_name}</b>!\n\n"
            f"Barcha universitetlar bazasi va sun'iy intellektga asoslangan imkoniyatlarni baholash tizimi tayyor.\n"
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
# 📢 ADMIN UCHUN E'LON TARQATISH (/elon)
# ==========================================
@dp.message(Command("elon"))
async def elon_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("📣 <b>E'lon tarqatish bo'limi!</b>\n\nBarcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni (matn, rasm, video yoki havola) shu yerga tashlang:")
    await state.set_state(BroadcastState.waiting_for_post)

@dp.message(BroadcastState.waiting_for_post)
async def elon_broadcast(message: types.Message, state: FSMContext):
    await message.answer("⏳ E'lon tarqatilmoqda, iltimos kuting...")
    
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            users = await cursor.fetchall()
            
    count = 0
    for user in users:
        try:
            # copy_to orqali jo'natsak mediya formatlar, tugmalar hammmasi xatosiz boradi
            await message.copy_to(chat_id=user[0])
            count += 1
            await asyncio.sleep(0.05) # Telegram limitiga tushmaslik uchun
        except Exception:
            pass # Bloklagan foydalanuvchilarni o'tkazib yuboradi
            
    await message.answer(f"✅ <b>E'lon muvaffaqiyatli tarqatildi!</b>\n👥 Jami qabul qildi: {count} ta foydalanuvchi.")
    await state.clear()

# ==========================================
# 📊 O'TISH BALLARI BO'LIMI
# ==========================================
@dp.message(F.text == "📊 O'tish ballari")
async def passing_scores(message: types.Message):
    await message.answer("📍 <b>Qaysi hududdagi</b> OTMlarni ko'rmoqchisiz? Ro'yxatdan tanlang:", reply_markup=get_regions_keyboard("reg"))

@dp.callback_query(F.data.startswith("reg_"))
async def show_otms_in_region(callback: types.CallbackQuery):
    region_id = callback.data.split("_")[1]
    reg_name = REGIONS_DB.get(region_id, {}).get("name", "Noma'lum hudud")
    await callback.message.edit_text(f"🏫 <b>{reg_name}</b> bo'yicha OTMlar:", reply_markup=get_otmlar_keyboard(region_id, "otm"))

@dp.callback_query(F.data == "back_to_regions")
async def back_to_regions(callback: types.CallbackQuery):
    await callback.message.edit_text("📍 <b>Qaysi hududdagi</b> OTMlarni ko'rmoqchisiz?", reply_markup=get_regions_keyboard("reg"))

@dp.callback_query(F.data.startswith("otm_"))
async def show_university_scores(callback: types.CallbackQuery):
    _, region_id, otm_id = callback.data.split("_")
    otm_data = REGIONS_DB[region_id]["otmlar"][otm_id]
    
    text = f"🏫 <b>{otm_data['name']}</b>\n\n"
    for yonalish in otm_data['yonalishlar']:
        text += (f"📌 <b>{yonalish['name']}</b>\n"
                 f"🟢 Grant: {yonalish['grant']} ball\n"
                 f"🟠 Kontrakt: {yonalish['kontrakt']} ball\n\n")
                 
    await callback.message.edit_text(text, reply_markup=get_otmlar_keyboard(region_id, "otm"))

# ==========================================
# 🎯 IMKONIYATNI BAHOLASH TIZIMI (ALGORITM)
# ==========================================
@dp.message(F.text == "🎯 Imkoniyatni baholash")
async def chance_start(message: types.Message):
    await message.answer("🎯 <b>Imkoniyatni baholash algoritmi</b>\n\nQaysi hududga topshirmoqchisiz?", reply_markup=get_regions_keyboard("chance_reg"))

@dp.callback_query(F.data.startswith("chance_reg_"))
async def chance_show_otm(callback: types.CallbackQuery):
    region_id = callback.data.replace("chance_reg_", "")
    await callback.message.edit_text("🏫 Endi Universitetni tanlang:", reply_markup=get_otmlar_keyboard(region_id, "chance_otm"))

@dp.callback_query(F.data == "chance_back_to_regions")
async def chance_back(callback: types.CallbackQuery):
    await callback.message.edit_text("🎯 Qaysi hududga topshirmoqchisiz?", reply_markup=get_regions_keyboard("chance_reg"))

@dp.callback_query(F.data.startswith("chance_otm_"))
async def chance_show_yonalish(callback: types.CallbackQuery):
    _, _, region_id, otm_id = callback.data.split("_")
    await callback.message.edit_text("📌 Yo'nalishni tanlang:", reply_markup=get_yonalishlar_keyboard(region_id, otm_id))

@dp.callback_query(F.data.startswith("chyon_"))
async def chance_ask_score(callback: types.CallbackQuery, state: FSMContext):
    _, region_id, otm_id, idx = callback.data.split("_")
    
    await state.update_data(chance_region=region_id, chance_otm=otm_id, chance_idx=int(idx))
    await callback.message.delete()
    await callback.message.answer("✏️ <b>O'zingizning joriy to'plagan (yoki taxminiy) balingizni kiriting:</b>\n<i>Masalan: 145.5</i>")
    await state.set_state(ChanceState.waiting_for_score)

@dp.message(ChanceState.waiting_for_score)
async def chance_calculate(message: types.Message, state: FSMContext):
    try:
        user_score = float(message.text)
    except ValueError:
        return await message.answer("⚠️ Iltimos, raqam ko'rinishida kiriting (Masalan: 125.4).")

    data = await state.get_data()
    region_id, otm_id, idx = data['chance_region'], data['chance_otm'], data['chance_idx']
    yonalish = REGIONS_DB[region_id]["otmlar"][otm_id]["yonalishlar"][idx]
    
    grant_score = yonalish['grant']
    kontrakt_score = yonalish['kontrakt']
    
    grant_chance = min(100, round((user_score / grant_score) * 100, 1)) if user_score < grant_score else 99.9
    kontrakt_chance = min(100, round((user_score / kontrakt_score) * 100, 1)) if user_score < kontrakt_score else 99.9
    
    grant_emoji = "🟢" if grant_chance > 80 else "🟡" if grant_chance > 50 else "🔴"
    kontrakt_emoji = "🟢" if kontrakt_chance > 80 else "🟡" if kontrakt_chance > 50 else "🔴"

    text = (f"🎯 <b>Algoritmik Prognoz Natijasi</b>\n\n"
            f"🏫 OTM: <b>{REGIONS_DB[region_id]['otmlar'][otm_id]['name']}</b>\n"
            f"📌 Yo'nalish: <b>{yonalish['name']}</b>\n"
            f"🔢 Sizning balingiz: <b>{user_score}</b>\n\n"
            f"📊 <b>Kirish ehtimolligi:</b>\n"
            f"{grant_emoji} Davlat granti: <b>{grant_chance}%</b> <i>(Talab: {grant_score})</i>\n"
            f"{kontrakt_emoji} To'lov-kontrakt: <b>{kontrakt_chance}%</b> <i>(Talab: {kontrakt_score})</i>\n\n"
            f"<i>💡 Eslatma: Bu tahlil o'tgan yilgi statikaga asoslangan bo'lib, joriy yilgi abituriyentlar bilim darajasiga qarab farq qilishi mumkin.</i>")
            
    await message.answer(text, reply_markup=main_menu)
    await state.clear()

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
# BOSHQA BO'LIMLAR VA BALL HISOBLAGICH
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
    btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🚀 Testlarni ishlash", url=f"https://t.me/{TEST_BOT[1:]}")]])
    await message.answer(f"🔥 Haqiqiy DTM savollari bilan bellashing!\nSizga maxsus <b>{TEST_BOT}</b> ni tavsiya qilamiz!", reply_markup=btn)

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
# ⚙️ ISHGA TUSHIRISH
# ==========================================
async def main():
    await init_db() 
    logging.basicConfig(level=logging.INFO)
    print("🚀 Mandat Bot ishga tushdi! /elon komandasi tayyor.")
    
    asyncio.create_task(auto_news_parser())
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")