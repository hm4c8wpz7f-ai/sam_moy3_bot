import os
import random

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# =========================
# SETTINGS
# =========================

TOKEN = os.environ.get("BOT_TOKEN")

ADMIN_ID = 5920169684

(
    LANG,
    PRODUCT,
    QUANTITY,
    PAYMENT,
    PHONE,
    LOCATION,
) = range(6)

# =========================
# PRODUCTS
# =========================

products = {
    "uz": [
        "🧴 Pena 20L",
        "🧪 Aktiv kimyo 20L",
    ],

    "ru": [
        "🧴 Пена 20Л",
        "🧪 Активная химия 20Л",
    ]
}

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["cart"] = []

    keyboard = [
        ["🇺🇿 O'zbekcha", "🇷🇺 Русский"]
    ]

    await update.message.reply_text(
        "Tilni tanlang / Выберите язык",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

    return LANG

# =========================
# LANGUAGE
# =========================

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if "🇺🇿" in text:

        context.user_data["lang"] = "uz"

        keyboard = [
            [products["uz"][0]],
            [products["uz"][1]],
            ["➡️ Keyingi"]
        ]

        await update.message.reply_text(
            "🛒 Mahsulot tanlang:",
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
            ["➡️ Далее"]
        ]

        await update.message.reply_text(
            "🛒 Выберите товар:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True
            )
        )

    return PRODUCT

# =========================
# PRODUCT
# =========================

async def product(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    lang = context.user_data["lang"]

    # NEXT
    if "keyingi" in text.lower() or "далее" in text.lower():

        if len(context.user_data["cart"]) == 0:

            if lang == "uz":
                await update.message.reply_text(
                    "❌ Avval mahsulot tanlang!"
                )
            else:
                await update.message.reply_text(
                    "❌ Сначала выберите товар!"
                )

            return PRODUCT

        # PAYMENT
        if lang == "uz":

            keyboard = [
                ["💵 Naqd"],
                ["💳 Plastik karta"]
            ]

            await update.message.reply_text(
                "💳 To'lov turini tanlang:",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard,
                    resize_keyboard=True
                )
            )

        else:

            keyboard = [
                ["💵 Наличные"],
                ["💳 Карта"]
            ]

            await update.message.reply_text(
                "💳 Выберите тип оплаты:",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard,
                    resize_keyboard=True
                )
            )

        return PAYMENT

    # SAVE PRODUCT
    context.user_data["current_product"] = text

    if lang == "uz":

        await update.message.reply_text(
            "🔢 Nechta kerak?"
        )

    else:

        await update.message.reply_text(
            "🔢 Сколько нужно?"
        )

    return QUANTITY

# =========================
# QUANTITY
# =========================

async def quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):

    qty = update.message.text.strip()

    lang = context.user_data["lang"]

    # ONLY NUMBER
    if not qty.isdigit():

        if lang == "uz":
            txt = "❌ To'g'ri raqam kiriting!"
        else:
            txt = "❌ Введите правильное число!"

        await update.message.reply_text(txt)

        return QUANTITY

    product_name = context.user_data["current_product"]

    context.user_data["cart"].append(
        f"{product_name} — {qty} dona"
    )

    # KEYBOARD
    if lang == "uz":

        keyboard = [
            [products["uz"][0]],
            [products["uz"][1]],
            ["➡️ Keyingi"]
        ]

        txt = (
            "✅ Mahsulot qo'shildi.\n\n"
            "Yana mahsulot tanlang yoki davom eting:"
        )

    else:

        keyboard = [
            [products["ru"][0]],
            [products["ru"][1]],
            ["➡️ Далее"]
        ]

        txt = (
            "✅ Товар добавлен.\n\n"
            "Добавьте товар или продолжите:"
        )

    await update.message.reply_text(
        txt,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

    return PRODUCT

# =========================
# PAYMENT
# =========================

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

        await update.message.reply_text(
            "📞 Telefon raqamingizni yuboring:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )

    else:

        keyboard = [[
            KeyboardButton(
                "📞 Отправить номер",
                request_contact=True
            )
        ]]

        await update.message.reply_text(
            "📞 Отправьте номер телефона:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )

    return PHONE

# =========================
# PHONE
# =========================

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

        await update.message.reply_text(
            "📍 Lokatsiyani yuboring:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )

    else:

        keyboard = [[
            KeyboardButton(
                "📍 Отправить локацию",
                request_location=True
            )
        ]]

        await update.message.reply_text(
            "📍 Отправьте локацию:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )

    return LOCATION

# =========================
# LOCATION
# =========================

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):

    lat = update.message.location.latitude
    lon = update.message.location.longitude

    order_id = random.randint(1000, 9999)

    products_text = "\n".join(
        context.user_data["cart"]
    )

    text = f"""
🆕 YANGI BUYURTMA #{order_id}

🛒 Mahsulotlar:
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

    lang = context.user_data["lang"]

    if lang == "uz":
        done_text = (
            f"✅ Buyurtmangiz qabul qilindi!\n\n"
            f"🆔 Buyurtma raqami: #{order_id}"
        )

        keyboard = [["🛒 Yangi buyurtma"]]

    else:
        done_text = (
            f"✅ Заказ принят!\n\n"
            f"🆔 Номер заказа: #{order_id}"
        )

        keyboard = [["🛒 Новый заказ"]]

    await update.message.reply_text(
        done_text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

    context.user_data["cart"] = []

    return ConversationHandler.END

# =========================
# NEW ORDER
# =========================

async def new_order(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["cart"] = []

    lang = context.user_data.get("lang", "uz")

    if lang == "uz":

        keyboard = [
            [products["uz"][0]],
            [products["uz"][1]],
            ["➡️ Keyingi"]
        ]

        await update.message.reply_text(
            "🛒 Mahsulot tanlang:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True
            )
        )

    else:

        keyboard = [
            [products["ru"][0]],
            [products["ru"][1]],
            ["➡️ Далее"]
        ]

        await update.message.reply_text(
            "🛒 Выберите товар:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True
            )
        )

    return PRODUCT

# =========================
# CANCEL
# =========================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "❌ Bekor qilindi",
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

# =========================
# MAIN
# =========================

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(

        entry_points=[

            CommandHandler("start", start),

            MessageHandler(
                filters.TEXT & filters.Regex("🛒 Yangi buyurtma"),
                new_order
            ),

            MessageHandler(
                filters.TEXT & filters.Regex("🛒 Новый заказ"),
                new_order
            ),
        ],

        states={

            LANG: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    language
                )
            ],

            PRODUCT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    product
                )
            ],

            QUANTITY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    quantity
                )
            ],

            PAYMENT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    payment
                )
            ],

            PHONE: [
                MessageHandler(
                    filters.CONTACT,
                    phone
                )
            ],

            LOCATION: [
                MessageHandler(
                    filters.LOCATION,
                    location
                )
            ],
        },

        fallbacks=[
            CommandHandler("cancel", cancel)
        ],
    )

    app.add_handler(conv_handler)

    print("Bot ishga tushdi...")

    app.run_polling()

# =========================

if __name__ == "__main__":
    main()
