from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import os

TOKEN = os.environ.get("BOT_TOKEN")

# O'zingizning Telegram ID
ADMIN_ID = 5920169684

(
    LANGUAGE,
    PRODUCT,
    QUANTITY,
    ADD_MORE,
    PAYMENT,
    PHONE,
    LOCATION,
) = range(7)


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        ["🇺🇿 O'zbekcha", "🇷🇺 Русский"]
    ]

    await update.message.reply_text(
        "Tilni tanlang / Выберите язык",
        reply_markup=ReplyKeyboardMarkup(
            buttons,
            resize_keyboard=True
        )
    )

    context.user_data["cart"] = []

    return LANGUAGE


# LANGUAGE
async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "🇺🇿" in text:
        context.user_data["lang"] = "uz"

        buttons = [
            ["🧴 Пена 20L"],
            ["🧼 Актив химия 20L"]
        ]

        await update.message.reply_text(
            "Маҳсулотни танланг:",
            reply_markup=ReplyKeyboardMarkup(
                buttons,
                resize_keyboard=True
            )
        )

    else:
        context.user_data["lang"] = "ru"

        buttons = [
            ["🧴 Пена 20L"],
            ["🧼 Актив химия 20L"]
        ]

        await update.message.reply_text(
            "Выберите товар:",
            reply_markup=ReplyKeyboardMarkup(
                buttons,
                resize_keyboard=True
            )
        )

    return PRODUCT


# PRODUCT
async def product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["current_product"] = update.message.text

    lang = context.user_data["lang"]

    if lang == "uz":
        await update.message.reply_text(
            "Миқдорини киритинг:"
        )
    else:
        await update.message.reply_text(
            "Введите количество:"
        )

    return QUANTITY


# QUANTITY
async def quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quantity = update.message.text
    product = context.user_data["current_product"]

    context.user_data["cart"].append({
        "product": product,
        "quantity": quantity
    })

    buttons = [
        ["➕ Yana mahsulot"],
        ["✅ Davom etish"]
    ]

    await update.message.reply_text(
        "Yana mahsulot qo'shasizmi?",
        reply_markup=ReplyKeyboardMarkup(
            buttons,
            resize_keyboard=True
        )
    )

    return ADD_MORE


# ADD MORE
async def add_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "Yana" in text:
        buttons = [
            ["🧴 Пена 20L"],
            ["🧼 Актив химия 20L"]
        ]

        await update.message.reply_text(
            "Маҳсулотни танланг:",
            reply_markup=ReplyKeyboardMarkup(
                buttons,
                resize_keyboard=True
            )
        )

        return PRODUCT

    buttons = [
        ["💵 Naqd"],
        ["💳 Plastik karta"]
    ]

    await update.message.reply_text(
        "Тўлов турини танланг:",
        reply_markup=ReplyKeyboardMarkup(
            buttons,
            resize_keyboard=True
        )
    )

    return PAYMENT


# PAYMENT
async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["payment"] = update.message.text

    button = KeyboardButton(
        "📞 Telefon raqam yuborish",
        request_contact=True
    )

    await update.message.reply_text(
        "Телефон рақамингизни юборинг:",
        reply_markup=ReplyKeyboardMarkup(
            [[button]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

    return PHONE


# PHONE
async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact

    context.user_data["phone"] = contact.phone_number

    button = KeyboardButton(
        "📍 Lokatsiya yuborish",
        request_location=True
    )

    await update.message.reply_text(
        "Локация юборинг:",
        reply_markup=ReplyKeyboardMarkup(
            [[button]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

    return LOCATION


# LOCATION
async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location

    cart = context.user_data["cart"]
    payment = context.user_data["payment"]
    phone = context.user_data["phone"]

    items_text = ""

    for item in cart:
        items_text += (
            f"🧴 {item['product']} - "
            f"{item['quantity']} dona\n"
        )

    text = f"""
🛒 YANGI BUYURTMA

{items_text}

💳 To'lov: {payment}
📞 Telefon: {phone}

📍 Lokatsiya:
https://maps.google.com/?q={loc.latitude},{loc.longitude}
"""

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=text
    )

    await update.message.reply_text(
        "✅ Buyurtmangiz qabul qilindi!",
        reply_markup=ReplyKeyboardRemove()
    )

    context.user_data.clear()

    return ConversationHandler.END


# CANCEL
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Bekor qilindi",
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


# MAIN
def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [
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

            ADD_MORE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    add_more
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

        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
