import asyncio
import logging
import os
import re

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 5920169684  # <-- admin id

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=BOT_TOKEN,
    parse_mode=ParseMode.HTML
)

dp = Dispatcher(storage=MemoryStorage())

# =========================
# DATA
# =========================

PRODUCTS = {
    "Пена 20л": 350000,
    "Актив химия 20л": 380000,
}

orders_db = {}
order_counter = 8157

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
# KEYBOARDS
# =========================

def lang_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🇺🇿 O'zbekcha"),
                KeyboardButton(text="🇷🇺 Русский")
            ]
        ],
        resize_keyboard=True
    )

def product_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пена 20л")],
            [KeyboardButton(text="Актив химия 20л")],
            [KeyboardButton(text="✅ Keyingi")]
        ],
        resize_keyboard=True
    )

def payment_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💵 Naqd"),
                KeyboardButton(text="💳 Plastik karta")
            ]
        ],
        resize_keyboard=True
    )

def phone_keyboard():
    return ReplyKeyboardMarkup(
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

def location_keyboard():
    return ReplyKeyboardMarkup(
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

def restart_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Yangi buyurtma berish")]
        ],
        resize_keyboard=True
    )

# =========================
# START
# =========================

@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "🇺🇿 Tilni tanlang\n🇷🇺 Выберите язык",
        reply_markup=lang_keyboard()
    )

    await state.set_state(OrderState.language)

# =========================
# LANGUAGE
# =========================

@dp.message(OrderState.language)
async def language_handler(message: Message, state: FSMContext):

    if message.text not in ["🇺🇿 O'zbekcha", "🇷🇺 Русский"]:
        await message.answer("❌ Tugmadan foydalaning")
        return

    await state.update_data(
        language=message.text,
        products=[]
    )

    await message.answer(
        "🧴 Mahsulot tanlang",
        reply_markup=product_keyboard()
    )

    await state.set_state(OrderState.product)

# =========================
# PRODUCT
# =========================

@dp.message(OrderState.product)
async def product_handler(message: Message, state: FSMContext):

    text = message.text

    if text == "✅ Keyingi":

        data = await state.get_data()

        if len(data["products"]) == 0:
            await message.answer(
                "❌ Avval mahsulot tanlang"
            )
            return

        await state.update_data(current_qty_index=0)

        first_product = data["products"][0]["name"]

        await message.answer(
            f"🔢 {first_product} sonini kiriting:",
            reply_markup=ReplyKeyboardRemove()
        )

        await state.set_state(OrderState.quantity)

        return

    if text not in PRODUCTS:
        await message.answer(
            "❌ Tugmalardan foydalaning"
        )
        return

    data = await state.get_data()

    products = data["products"]

    products.append({
        "name": text
    })

    await state.update_data(products=products)

    await message.answer(
        f"✅ {text} qo'shildi\n\n"
        f"Yana mahsulot tanlang yoki\n"
        f"'✅ Keyingi' tugmasini bosing"
    )

# =========================
# QUANTITY
# =========================

@dp.message(OrderState.quantity)
async def quantity_handler(message: Message, state: FSMContext):

    text = message.text.strip()

    if not text.isdigit():
        await message.answer(
            "❌ To'g'ri raqam kiriting"
        )
        return

    qty = int(text)

    data = await state.get_data()

    products = data["products"]

    current_index = data.get("current_qty_index", 0)

    products[current_index]["qty"] = qty

    current_index += 1

    await state.update_data(
        products=products,
        current_qty_index=current_index
    )

    if current_index < len(products):

        next_product = products[current_index]["name"]

        await message.answer(
            f"🔢 {next_product} sonini kiriting:"
        )

        return

    await message.answer(
        "💳 To'lov turini tanlang",
        reply_markup=payment_keyboard()
    )

    await state.set_state(OrderState.payment)

# =========================
# PAYMENT
# =========================

@dp.message(OrderState.payment)
async def payment_handler(message: Message, state: FSMContext):

    if message.text not in ["💵 Naqd", "💳 Plastik karta"]:
        await message.answer("❌ Tugmadan foydalaning")
        return

    await state.update_data(payment=message.text)

    await message.answer(
        "📞 Telefon raqamingizni yuboring",
        reply_markup=phone_keyboard()
    )

    await state.set_state(OrderState.phone)

# =========================
# PHONE
# =========================

@dp.message(OrderState.phone, F.contact)
async def phone_handler(message: Message, state: FSMContext):

    phone = message.contact.phone_number

    await state.update_data(phone=phone)

    await message.answer(
        "📍 Lokatsiyani yuboring",
        reply_markup=location_keyboard()
    )

    await state.set_state(OrderState.location)

# =========================
# LOCATION
# =========================

@dp.message(OrderState.location, F.location)
async def location_handler(message: Message, state: FSMContext):

    global order_counter

    data = await state.get_data()

    lat = message.location.latitude
    lon = message.location.longitude

    products_text = "\n".join(
        [
            f"• {p['name']} x {p['qty']}"
            for p in data["products"]
        ]
    )

    text = (
        f"🆕 <b>YANGI BUYURTMA #{order_counter}</b>\n\n"
        f"🧴 <b>Mahsulotlar:</b>\n"
        f"{products_text}\n\n"
        f"💳 <b>To'lov:</b> {data['payment']}\n"
        f"📞 <b>Telefon:</b> {data['phone']}\n\n"
        f"📍 <b>Yandex Navigator:</b>\n"
        f"https://yandex.ru/maps/?pt={lon},{lat}&z=16&l=map"
    )

    await bot.send_message(
        ADMIN_ID,
        text
    )

    orders_db[order_counter] = message.from_user.id

    order_counter += 1

    await message.answer(
        "✅ Buyurtmangiz qabul qilindi!",
        reply_markup=restart_keyboard()
    )

    await state.clear()

# =========================
# NEW ORDER
# =========================

@dp.message(F.text == "🛒 Yangi buyurtma berish")
async def new_order(message: Message, state: FSMContext):

    await state.clear()

    await message.answer(
        "🇺🇿 Tilni tanlang\n🇷🇺 Выберите язык",
        reply_markup=lang_keyboard()
    )

    await state.set_state(OrderState.language)

# =========================
# ADMIN REPLY
# =========================

@dp.message(F.reply_to_message)
async def admin_reply(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    reply_text = message.reply_to_message.text

    match = re.search(r'#(\d+)', reply_text)

    if not match:
        await message.answer(
            "❌ Buyurtma ID topilmadi"
        )
        return

    order_id = int(match.group(1))

    if order_id not in orders_db:
        await message.answer(
            "❌ Buyurtma topilmadi"
        )
        return

    user_id = orders_db[order_id]

    await bot.send_message(
        user_id,
        f"📩 Admin javobi:\n\n{message.text}"
    )

    await message.answer(
        "✅ Javob yuborildi"
    )

# =========================
# RUN
# =========================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
