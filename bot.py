import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5920169684  # admin id

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher(storage=MemoryStorage())

# =========================
# PRODUCTS
# =========================

PRODUCTS_UZ = [
    "Пена 20л",
    "Актив химия 20л",
    "Шампунь 20л",
    "Воск 20л"
]

PRODUCTS_RU = [
    "Пена 20л",
    "Актив химия 20л",
    "Шампунь 20л",
    "Воск 20л"
]

# =========================
# STATES
# =========================

class OrderState(StatesGroup):
    language = State()
    product = State()
    quantity = State()
    payment = State()
    phone = State()
    location = State()

# =========================
# START
# =========================

@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🇺🇿 O'zbekcha"),
                KeyboardButton(text="🇷🇺 Русский")
            ]
        ],
        resize_keyboard=True
    )

    await state.clear()

    await message.answer(
        "Tilni tanlang / Выберите язык",
        reply_markup=kb
    )

    await state.set_state(OrderState.language)

# =========================
# LANGUAGE
# =========================

@dp.message(OrderState.language)
async def language_handler(message: Message, state: FSMContext):

    text = message.text

    if text == "🇺🇿 O'zbekcha":
        lang = "uz"
        products = PRODUCTS_UZ
        msg = "🧴 Mahsulot tanlang"
    else:
        lang = "ru"
        products = PRODUCTS_RU
        msg = "🧴 Выберите товар"

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=p)] for p in products
        ] + [
            [KeyboardButton(text="✅ Keyingi")]
        ],
        resize_keyboard=True
    )

    await state.update_data(
        lang=lang,
        cart=[]
    )

    await message.answer(
        msg,
        reply_markup=kb
    )

    await state.set_state(OrderState.product)

# =========================
# PRODUCT
# =========================

@dp.message(OrderState.product)
async def product_handler(message: Message, state: FSMContext):

    text = message.text

    data = await state.get_data()

    lang = data.get("lang", "uz")

    products = PRODUCTS_UZ if lang == "uz" else PRODUCTS_RU

    # NEXT
    if text == "✅ Keyingi":

        cart = data.get("cart", [])

        if len(cart) == 0:
            await message.answer("❌ Avval mahsulot tanlang")
            return

        kb = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="💵 Naqd"),
                    KeyboardButton(text="💳 Karta")
                ]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "💳 To'lov turini tanlang:",
            reply_markup=kb
        )

        await state.set_state(OrderState.payment)
        return

    # PRODUCT
    if text not in products:
        await message.answer("❌ Tugmalardan foydalaning")
        return

    await state.update_data(current_product=text)

    await message.answer(
        "🔢 Mahsulot sonini kiriting:",
        reply_markup=ReplyKeyboardRemove()
    )

    await state.set_state(OrderState.quantity)

# =========================
# QUANTITY
# =========================

@dp.message(OrderState.quantity)
async def quantity_handler(message: Message, state: FSMContext):

    if not message.text.isdigit():
        await message.answer("❌ To'g'ri raqam kiriting")
        return

    qty = int(message.text)

    data = await state.get_data()

    cart = data.get("cart", [])
    product = data.get("current_product")
    lang = data.get("lang", "uz")

    cart.append({
        "product": product,
        "qty": qty
    })

    await state.update_data(cart=cart)

    products = PRODUCTS_UZ if lang == "uz" else PRODUCTS_RU

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=p)] for p in products
        ] + [
            [KeyboardButton(text="✅ Keyingi")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        f"✅ {product} qo'shildi\n\n"
        "Yana mahsulot tanlang yoki\n"
        "✅ Keyingi tugmasini bosing",
        reply_markup=kb
    )

    await state.set_state(OrderState.product)

# =========================
# PAYMENT
# =========================

@dp.message(OrderState.payment)
async def payment_handler(message: Message, state: FSMContext):

    payment = message.text

    await state.update_data(payment=payment)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📞 Telefon raqam yuborish",
                    request_contact=True
                )
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "📞 Telefon raqamingizni yuboring:",
        reply_markup=kb
    )

    await state.set_state(OrderState.phone)

# =========================
# PHONE
# =========================

@dp.message(OrderState.phone)
async def phone_handler(message: Message, state: FSMContext):

    if not message.contact:
        await message.answer("❌ Telefon raqamni tugma orqali yuboring")
        return

    phone = message.contact.phone_number

    await state.update_data(phone=phone)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📍 Lokatsiya yuborish",
                    request_location=True
                )
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "📍 Lokatsiyani yuboring:",
        reply_markup=kb
    )

    await state.set_state(OrderState.location)

# =========================
# LOCATION
# =========================

@dp.message(OrderState.location)
async def location_handler(message: Message, state: FSMContext):

    if not message.location:
        await message.answer("❌ Lokatsiyani tugma orqali yuboring")
        return

    lat = message.location.latitude
    lon = message.location.longitude

    data = await state.get_data()

    cart = data.get("cart", [])
    payment = data.get("payment")
    phone = data.get("phone")

    order_id = message.message_id

    products_text = ""

    for item in cart:
        products_text += (
            f"• {item['product']} x {item['qty']}\n"
        )

    yandex_link = f"https://yandex.ru/maps/?pt={lon},{lat}&z=16&l=map"

    text = (
        f"🛒 <b>YANGI BUYURTMA #{order_id}</b>\n\n"
        f"<b>Mahsulotlar:</b>\n"
        f"{products_text}\n"
        f"<b>To'lov:</b> {payment}\n"
        f"<b>Telefon:</b> {phone}\n\n"
        f"📍 <b>Yandex Navigator:</b>\n"
        f"{yandex_link}"
    )

    await bot.send_message(
        ADMIN_ID,
        text
    )

    await message.answer_location(lat, lon)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Yangi buyurtma berish")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "✅ Buyurtmangiz qabul qilindi",
        reply_markup=kb
    )

    await state.clear()

# =========================
# NEW ORDER
# =========================

@dp.message(F.text == "🛒 Yangi buyurtma berish")
async def new_order(message: Message, state: FSMContext):

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🇺🇿 O'zbekcha"),
                KeyboardButton(text="🇷🇺 Русский")
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "Tilni tanlang / Выберите язык",
        reply_markup=kb
    )

    await state.set_state(OrderState.language)

# =========================
# RUN
# =========================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
