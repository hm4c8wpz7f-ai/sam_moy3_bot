import os
import random
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

TOKEN = os.environ.get("BOT_TOKEN")

ADMIN_ID = 5920169684

LANG, PRODUCT, QUANTITY, PAYMENT, PHONE, LOCATION = range(6)

products = {
    "uz": [
        "🧴 Pena 20L",
        "🧪 Aktiv kimyo 20L"
    ],
    "ru": [
        "🧴 Пена 20Л",
        "🧪 Активная химия 20Л"
    ]
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🇺🇿 O'zbekcha", "🇷🇺 Русский"]]

    await update.message.reply_text(
        "Tilni tanlang / Выберите язык",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

    context.user_data["cart"] = []

    return LANG


async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "🇺🇿" in text:
        context.user_data["lang"] = "uz"

        keyboard = [
            [products["uz"][0]],
            [products["uz"][1]],
            ["✅ Buyurtmani yakunlash"]
        ]

        await update.message.reply_text(
            "Mahsulot tanlang:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True
            )
        )

    else:
        context.user_data["lang"] = "ru"

        keyboard = [
            [products["ru"][0]],
            [products["ru"][1]],
            ["✅ Завершить заказ"]
        ]

        await update.message.reply_text(
            "Выберите товар:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True
            )
        )

    return PRODUCT


async def product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "yakunlash" in text.lower() or "завершить" in text.lower():

        if len(context.user_data["cart"]) == 0:
            await update.message.reply_text(
                "Avval mahsulot tanlang!"
            )
            return PRODUCT

        lang = context.user_data["lang"]

        if lang == "uz":
            keyboard = [["💵 Naqd", "💳 Karta"]]
            txt = "To'lov turini tanlang:"
        else:
            keyboard = [["💵 Наличные", "💳 Карта"]]
            txt = "Выберите тип оплаты:"

        await update.message.reply_text(
            txt,
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True
            )
        )

        return PAYMENT

    context.user_data["current_product"] = text

    lang = context.user_data["lang"]

    if lang == "uz":
        txt = "Nechta kerak?"
    else:
        txt = "Сколько нужно?"

    await update.message.reply_text(txt)

    return QUANTITY


async def quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    qty = update.message.text
    product_name = context.user_data["current_product"]

    context.user_data["cart"].append(
        f"{product_name} — {qty} dona"
    )

    lang = context.user_data["lang"]

    if lang == "uz":
        keyboard = [
            [products["uz"][0]],
            [products["uz"][1]],
            ["✅ Buyurtmani yakunlash"]
        ]

        txt = "Yana mahsulot tanlang yoki yakunlang:"
    else:
        keyboard = [
            [products["ru"][0]],
            [products["ru"][1]],
            ["✅ Завершить заказ"]
        ]

        txt = "Добавьте товар или завершите заказ:"

    await update.message.reply_text(
        txt,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

    return PRODUCT


async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["payment"] = update.message.text

    lang = context.user_data["lang"]

    if lang == "uz":
        keyboard = [[
            KeyboardButton(
                "📞 Telefon raqam yuborish",
                request_contact=True
            )
        ]]

        txt = "Telefon raqamingizni yuboring:"
    else:
        keyboard = [[
            KeyboardButton(
                "📞 Отправить номер",
                request_contact=True
            )
        ]]

        txt = "Отправьте номер телефона:"

    await update.message.reply_text(
        txt,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

    return PHONE


async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact.phone_number
    context.user_data["phone"] = contact

    lang = context.user_data["lang"]

    if lang == "uz":
        keyboard = [[
            KeyboardButton(
                "📍 Lokatsiya yuborish",
                request_location=True
            )
        ]]

        txt = "Lokatsiyani yuboring:"
    else:
        keyboard = [[
            KeyboardButton(
                "📍 Отправить локацию",
                request_location=True
            )
        ]]

        txt = "Отправьте локацию:"

    await update.message.reply_text(
        txt,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

    return LOCATION


async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lat = update.message.location.latitude
    lon = update.message.location.longitude

    order_id = random.randint(1000, 9999)

    products_text = "\n".join(
        context.user_data["cart"]
    )

    text = f"""
🆕 YANGI BUYURTMA #{order_id}

🧴 Mahsulotlar:
{products_text}

💳 To'lov:
{context.user_data['payment']}

📞 Telefon:
{context.user_data['phone']}

📍 Yandex Navigator:
https://yandex.ru/maps/?pt={lon},{lat}&z=16&l=map
"""

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=text
    )

    keyboard = [["🛒 Yangi buyurtma"]]

    await update.message.reply_text(
        f"✅ Buyurtmangiz qabul qilindi!\n\n🆔 Buyurtma: #{order_id}",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

    return ConversationHandler.END


async def new_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cart"] = []

    lang = context.user_data.get("lang", "uz")

    if lang == "uz":
        keyboard = [
            [products["uz"][0]],
            [products["uz"][1]],
            ["✅ Buyurtmani yakunlash"]
        ]

        txt = "Mahsulot tanlang:"
    else:
        keyboard = [
            [products["ru"][0]],
            [products["ru"][1]],
            ["✅ Завершить заказ"]
        ]

        txt = "Выберите товар:"

    await update.message.reply_text(
        txt,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

    return PRODUCT


app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
        MessageHandler(
            filters.TEXT & filters.Regex("🛒 Yangi buyurtma"),
            new_order
        )
    ],

    states={
        LANG: [
            MessageHandler(filters.TEXT, language)
        ],

        PRODUCT: [
            MessageHandler(filters.TEXT, product)
        ],

        QUANTITY: [
            MessageHandler(filters.TEXT, quantity)
        ],

        PAYMENT: [
            MessageHandler(filters.TEXT, payment)
        ],

        PHONE: [
            MessageHandler(filters.CONTACT, phone)
        ],

        LOCATION: [
            MessageHandler(filters.LOCATION, location)
        ],
    },

    fallbacks=[]
)

app.add_handler(conv_handler)

print("Bot ishga tushdi...")

app.run_polling()
