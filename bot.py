import logging
import os
import json
from datetime import datetime, date
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "")
DATA_FILE = "talabномалар.json"

# Conversation states
MIB_NUM, HODIM, SUMMA, SANA, MUDDAT = range(5)
BAJARILDI_ID = 10

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def today_str():
    return date.today().isoformat()

def status_emoji(row):
    s = row.get("status", "wait")
    if s == "done":
        return "✅"
    if row.get("muddat") and row["muddat"] < today_str():
        return "🔴"
    return "🟡"

def format_row(i, row):
    emoji = status_emoji(row)
    status_text = "Бажарилди" if row.get("status") == "done" else (
        "Муддати ўтган" if row.get("muddat") and row["muddat"] < today_str() else "Кутилмоқда"
    )
    return (
        f"{i}. {emoji} <b>{row['mib_num']}</b>\n"
        f"   👤 {row['hodim']}\n"
        f"   💰 {int(row['summa']):,} сўм\n"
        f"   📅 {row.get('sana','—')}  ⏰ Муддат: {row.get('muddat','—')}\n"
        f"   📌 {status_text}\n"
    )

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("➕ Янги талабнома"), KeyboardButton("📋 Барча рўйхат")],
    [KeyboardButton("📅 Бугун"), KeyboardButton("🟡 Кутилмоқда")],
    [KeyboardButton("🔴 Муддати ўтган"), KeyboardButton("✅ Бажарилди қилиш")],
    [KeyboardButton("📊 Статистика")]
], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>МИБ Талабномалари Назорат</b> ботига хуш келибсиз!\n\n"
        "Қуйидаги тугмалардан фойдаланинг:",
        parse_mode="HTML",
        reply_markup=main_keyboard
    )

async def statistika(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    t = today_str()
    total = len(data)
    bugun = sum(1 for r in data if r.get("sana") == t)
    kutilmoqda = sum(1 for r in data if r.get("status") != "done" and (not r.get("muddat") or r["muddat"] >= t))
    otgan = sum(1 for r in data if r.get("status") != "done" and r.get("muddat") and r["muddat"] < t)
    bajarildi = sum(1 for r in data if r.get("status") == "done")

    await update.message.reply_text(
        f"📊 <b>Статистика</b>\n\n"
        f"📁 Жами: <b>{total}</b>\n"
        f"🆕 Бугун: <b>{bugun}</b>\n"
        f"🟡 Кутилмоқда: <b>{kutilmoqda}</b>\n"
        f"🔴 Муддати ўтган: <b>{otgan}</b>\n"
        f"✅ Бажарилди: <b>{bajarildi}</b>",
        parse_mode="HTML",
        reply_markup=main_keyboard
    )

async def royxat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text("📭 Талабномалар йўқ.", reply_markup=main_keyboard)
        return
    text = "📋 <b>Барча талабномалар:</b>\n\n"
    for i, row in enumerate(data, 1):
        text += format_row(i, row)
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=main_keyboard)

async def bugun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    t = today_str()
    rows = [r for r in data if r.get("sana") == t]
    if not rows:
        await update.message.reply_text("📭 Бугун янги талабнома йўқ.", reply_markup=main_keyboard)
        return
    text = f"📅 <b>Бугунги талабномалар ({t}):</b>\n\n"
    for i, row in enumerate(rows, 1):
        text += format_row(i, row)
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=main_keyboard)

async def kutilmoqda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    t = today_str()
    rows = [r for r in data if r.get("status") != "done" and (not r.get("muddat") or r["muddat"] >= t)]
    if not rows:
        await update.message.reply_text("✅ Кутилаётган талабномалар йўқ!", reply_markup=main_keyboard)
        return
    text = "🟡 <b>Кутилмоқда:</b>\n\n"
    for i, row in enumerate(rows, 1):
        text += format_row(i, row)
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=main_keyboard)

async def muddat_otgan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    t = today_str()
    rows = [r for r in data if r.get("status") != "done" and r.get("muddat") and r["muddat"] < t]
    if not rows:
        await update.message.reply_text("✅ Муддати ўтган талабномалар йўқ!", reply_markup=main_keyboard)
        return
    text = "🔴 <b>Муддати ўтган:</b>\n\n"
    for i, row in enumerate(rows, 1):
        text += format_row(i, row)
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=main_keyboard)

# --- Yangi talabнома qo'shish ---
async def yangi_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "📝 <b>Янги талабнома қўшиш</b>\n\n"
        "1️⃣ МИБ рақамини киритинг:\n(масалан: МИБ-2024-001)",
        parse_mode="HTML"
    )
    return MIB_NUM

async def get_mib_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mib_num"] = update.message.text.strip()
    await update.message.reply_text("2️⃣ Ходим исми ва фамилиясини киритинг:")
    return HODIM

async def get_hodim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["hodim"] = update.message.text.strip()
    await update.message.reply_text("3️⃣ Қарз суммасини киритинг (сўмда, фақат рақам):")
    return SUMMA

async def get_summa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        summa = int(update.message.text.strip().replace(" ", "").replace(",", ""))
        context.user_data["summa"] = summa
    except ValueError:
        await update.message.reply_text("❌ Фақат рақам киритинг. Қайтадан:")
        return SUMMA
    await update.message.reply_text(
        f"4️⃣ Талабнома санасини киритинг:\n(формат: {today_str()}, ёки бугун учун <b>бугун</b> деб ёзинг)",
        parse_mode="HTML"
    )
    return SANA

async def get_sana(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip().lower()
    if txt in ("бугун", "bugun", "today"):
        context.user_data["sana"] = today_str()
    else:
        context.user_data["sana"] = txt
    await update.message.reply_text(
        "5️⃣ Тўлов муддатини киритинг:\n(формат: 2024-12-31, ёки йўқ бўлса <b>йўқ</b> деб ёзинг)",
        parse_mode="HTML"
    )
    return MUDDAT

async def get_muddat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip().lower()
    context.user_data["muddat"] = "" if txt in ("йўқ", "yo'q", "yoq", "-") else txt

    row = {
        "id": str(int(datetime.now().timestamp())),
        "mib_num": context.user_data["mib_num"],
        "hodim": context.user_data["hodim"],
        "summa": context.user_data["summa"],
        "sana": context.user_data["sana"],
        "muddat": context.user_data["muddat"],
        "status": "wait"
    }
    data = load_data()
    data.insert(0, row)
    save_data(data)

    await update.message.reply_text(
        f"✅ <b>Талабнома сақланди!</b>\n\n"
        f"🔢 {row['mib_num']}\n"
        f"👤 {row['hodim']}\n"
        f"💰 {row['summa']:,} сўм\n"
        f"📅 {row['sana']}  ⏰ {row['muddat'] or '—'}",
        parse_mode="HTML",
        reply_markup=main_keyboard
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Бекор қилинди.", reply_markup=main_keyboard)
    return ConversationHandler.END

# --- Bajarildi ---
async def bajarildi_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    active = [r for r in data if r.get("status") != "done"]
    if not active:
        await update.message.reply_text("✅ Барча талабномалар бажарилган!", reply_markup=main_keyboard)
        return ConversationHandler.END
    text = "✅ <b>Қайси талабнома бажарилди?</b>\nРақамини киритинг:\n\n"
    for i, row in enumerate(active, 1):
        text += f"{i}. {row['mib_num']} — {row['hodim']}\n"
    context.user_data["active"] = active
    await update.message.reply_text(text, parse_mode="HTML")
    return BAJARILDI_ID

async def bajarildi_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        idx = int(update.message.text.strip()) - 1
        active = context.user_data.get("active", [])
        row = active[idx]
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Нотўғри рақам. Қайтадан киритинг:")
        return BAJARILDI_ID

    data = load_data()
    for r in data:
        if r["id"] == row["id"]:
            r["status"] = "done"
    save_data(data)
    await update.message.reply_text(
        f"✅ <b>{row['mib_num']}</b> — {row['hodim']}\nБажарилди деб белгиланди!",
        parse_mode="HTML",
        reply_markup=main_keyboard
    )
    return ConversationHandler.END

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📋 Барча рўйхат":
        await royxat(update, context)
    elif text == "📅 Бугун":
        await bugun(update, context)
    elif text == "🟡 Кутилмоқда":
        await kutilmoqda(update, context)
    elif text == "🔴 Муддати ўтган":
        await muddat_otgan(update, context)
    elif text == "📊 Статистика":
        await statistika(update, context)
    else:
        await update.message.reply_text("Тугмалардан фойдаланинг 👇", reply_markup=main_keyboard)

def main():
    app = Application.builder().token(TOKEN).build()

    yangi_conv = ConversationHandler(
        entry_points=[
            CommandHandler("yangi", yangi_start),
            MessageHandler(filters.Regex("^➕ Янги талабнома$"), yangi_start)
        ],
        states={
            MIB_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_mib_num)],
            HODIM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hodim)],
            SUMMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_summa)],
            SANA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_sana)],
            MUDDAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_muddat)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    bajarildi_conv = ConversationHandler(
        entry_points=[
            CommandHandler("bajarildi", bajarildi_start),
            MessageHandler(filters.Regex("^✅ Бажарилди қилиш$"), bajarildi_start)
        ],
        states={
            BAJARILDI_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, bajarildi_set)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("statistika", statistika))
    app.add_handler(CommandHandler("royxat", royxat))
    app.add_handler(CommandHandler("bugun", bugun))
    app.add_handler(yangi_conv)
    app.add_handler(bajarildi_conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
