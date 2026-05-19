import os
import asyncio
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

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5920169684  # admin telegram id

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher(storage=MemoryStorage())

# =========================
# PRODUCTS
# =========================

PRODUCTS = [
    "🧴 Пена 20 л",
    "🧪 Актив химия 20 л"
]

# =========================
# STATES
# =========================

class OrderState(StatesGroup):
    language = State()
    product = State()
    quantity = State()
    phone = State()
    location = State()

# =========================
# START
# =========================

@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):

    await state.clear()

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🇺🇿 Ўзбекча"),
                KeyboardButton(text="🇷🇺 Русский")
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "Тилни танланг / Выберите язык",
        reply_markup=kb
    )

    await state.set_state(OrderState.language)

# =========================
# LANGUAGE
# =========================

@dp.message(OrderState.language)
async def language_handler(message: Message, state: FSMContext):

    lang = "uz"

    if "Русский" in message.text:
        lang = "ru"

    await state.update_data(
        lang=lang,
        cart=[]
    )

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=p)] for p in PRODUCTS
        ] + [
            [KeyboardButton(text="✅ Кейинги")]
        ],
        resize_keyboard=True
    )

    text = "🧴 Маҳсулот танланг"

    if lang == "ru":
        text = "🧴 Выберите товар"

    await message.answer(
        text,
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

    # NEXT
    if text == "✅ Кейинги":

        cart = data.get("cart", [])

        if len(cart) == 0:
            await message.answer("❌ Аввал маҳсулот танланг")
            return

        kb = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text="📞 Телефон рақам юбориш",
                        request_contact=True
                    )
                ]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "📞 Телефон рақамингизни юборинг:",
            reply_markup=kb
        )

        await state.set_state(OrderState.phone)

        return

    # PRODUCT CHECK
    if text not in PRODUCTS:
        await message.answer("❌ Тугмалардан фойдаланинг")
        return

    await state.update_data(current_product=text)

    await message.answer(
        "🔢 Сонини киритинг:",
        reply_markup=ReplyKeyboardRemove()
    )

    await state.set_state(OrderState.quantity)

# =========================
# QUANTITY
# =========================

@dp.message(OrderState.quantity)
async def quantity_handler(message: Message, state: FSMContext):

    if not message.text.isdigit():
        await message.answer("❌ Тўғри рақам киритинг")
        return

    qty = int(message.text)

    data = await state.get_data()

    cart = data.get("cart", [])
    product = data.get("current_product")

    cart.append({
        "product": product,
        "qty": qty
    })

    await state.update_data(cart=cart)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=p)] for p in PRODUCTS
        ] + [
            [KeyboardButton(text="✅ Кейинги")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        f"✅ {product} қўшилди\n\n"
        "Яна маҳсулот танланг ёки\n"
        "✅ Кейинги тугмасини босинг",
        reply_markup=kb
    )

    await state.set_state(OrderState.product)

# =========================
# PHONE
# =========================

@dp.message(OrderState.phone)
async def phone_handler(message: Message, state: FSMContext):

    if not message.contact:
        await message.answer(
            "❌ Телефон рақамни тугма орқали юборинг"
        )
        return

    phone = message.contact.phone_number

    await state.update_data(phone=phone)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📍 Локация юбориш",
                    request_location=True
                )
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "📍 Локацияни юборинг:",
        reply_markup=kb
    )

    await state.set_state(OrderState.location)

# =========================
# LOCATION
# =========================

@dp.message(OrderState.location)
async def location_handler(message: Message, state: FSMContext):

    if not message.location:
        await message.answer(
            "❌ Локацияни тугма орқали юборинг"
        )
        return

    lat = message.location.latitude
    lon = message.location.longitude

    data = await state.get_data()

    cart = data.get("cart", [])
    phone = data.get("phone")

    order_id = message.message_id

    products_text = ""

    for item in cart:
        products_text += (
            f"• {item['product']} x {item['qty']}\n"
        )

    yandex_link = (
        f"https://yandex.ru/maps/?pt={lon},{lat}&z=16&l=map"
    )

    admin_text = (
        f"🛒 <b>ЯНГИ БУЮРТМА #{order_id}</b>\n\n"
        f"<b>Маҳсулотлар:</b>\n"
        f"{products_text}\n"
        f"<b>Телефон:</b> {phone}\n\n"
        f"📍 <b>Yandex Navigator:</b>\n"
        f"{yandex_link}"
    )

    sent_message = await bot.send_message(
        ADMIN_ID,
        admin_text
    )

    # save admin message id
    await state.update_data(
        admin_message_id=sent_message.message_id,
        customer_id=message.from_user.id
    )

    await message.answer_location(lat, lon)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Янги буюртма")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        f"✅ Буюртмангиз қабул қилинди\n"
        f"🆔 Буюртма рақами: #{order_id}",
        reply_markup=kb
    )

    await state.clear()

# =========================
# NEW ORDER
# =========================

@dp.message(F.text == "🛒 Янги буюртма")
async def new_order(message: Message, state: FSMContext):

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🇺🇿 Ўзбекча"),
                KeyboardButton(text="🇷🇺 Русский")
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "Тилни танланг / Выберите язык",
        reply_markup=kb
    )

    await state.set_state(OrderState.language)

# =========================
# ADMIN REPLY
# =========================

@dp.message(F.reply_to_message)
async def admin_reply(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    replied_text = message.reply_to_message.text

    if "ЯНГИ БУЮРТМА" not in replied_text:
        return

    try:
        lines = replied_text.split("\n")

        order_line = lines[0]

        order_number = order_line.split("#")[1]

        # customer id line search
        # temporary simple logic

        await message.answer(
            "✅ Жавоб юборилди"
        )

    except:
        pass

# =========================
# RUN
# =========================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
