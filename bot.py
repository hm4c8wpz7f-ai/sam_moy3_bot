import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart
 
# ──────────────────────────────────────────────
#  СОЗЛАШ (шу ерни тўлдиринг)
# ──────────────────────────────────────────────
BOT_TOKEN     = "8961849878:AAG5t12VRprPCw-WW-N7F0GFCMMBbR9Efck" 
ADMIN_CHAT_ID = 5920169684        
 
# ──────────────────────────────────────────────
#  ТОВАРЛАР (янги товар қўшиш учун шу рўйхатни кенгайтиринг)
# ──────────────────────────────────────────────
PRODUCTS = {
    "pena": {
        "emoji": "🧴",
        "uz": "Пена 20 л",
        "ru": "Пена 20 л",
    },
    "aktiv": {
        "emoji": "🧪",
        "uz": "Актив химия 20 л",
        "ru": "Актив химия 20 л",
    },
}
 
# ──────────────────────────────────────────────
#  МАТНЛАР
# ──────────────────────────────────────────────
T = {
    "uz": {
        "welcome":        "🛒 <b>СамМой маҳсулотлари</b>га хуш келибсиз!\n\nБуюртма бериш учун қуйидагилардан фойдаланинг 👇",
        "choose_product": "📦 Қайси маҳсулотни буюртма қилмоқчисиз?",
        "enter_qty":      "Нечта буюртма қиласиз? (Рақам киритинг)",
        "qty_error":      "❌ Илтимос, тўғри рақам киритинг (1–999)",
        "added":          "✅ Қўшилди: <b>{name}</b> — {qty} та",
        "cart_title":     "🛒 <b>Буюртмангиз:</b>",
        "cart_line":      "  • {emoji} {name} — {qty} та",
        "add_more":       "➕ Яна маҳсулот қўшиш",
        "next":           "➡️ Кейинги",
        "ask_phone":      "📞 Телефон рақамингизни юборинг:",
        "share_phone":    "📱 Рақамимни юбориш",
        "invalid_phone":  "❌ Нотўғри рақам. Қайтадан киритинг:",
        "ask_location":   "📍 Манзилингизни юборинг (геолокация ёки матн билан):",
        "share_loc":      "📍 Локациямни юбориш",
        "confirm_title":  "📋 <b>Буюртмани тасдиқланг:</b>",
        "confirm_phone":  "📞 Телефон: <code>{phone}</code>",
        "confirm_loc":    "📍 Манзил: {loc}",
        "btn_confirm":    "✅ Тасдиқлаш",
        "btn_cancel":     "❌ Бекор қилиш",
        "order_sent":     "🎉 <b>Буюртмангиз #{order_id} қабул қилинди!</b>\nОператор тез орада сиз билан боғланади.",
        "cancelled":      "❌ Буюртма бекор қилинди.",
        "new_order":      "🛒 Янги буюртма",
        "change_lang":    "🌐 Тилни ўзгартириш",
        # Админ жавоби
        "reply_sent":     "✅ Жавобингиз мижозга юборилди.",
        "reply_fail":     "❌ Жавоб юборишда хато.",
    },
    "ru": {
        "welcome":        "🛒 Добро пожаловать в <b>СамМой Продукты</b>!\n\nДля оформления заказа воспользуйтесь меню ниже 👇",
        "choose_product": "📦 Какой продукт хотите заказать?",
        "enter_qty":      "Сколько единиц? (Введите число)",
        "qty_error":      "❌ Пожалуйста, введите корректное число (1–999)",
        "added":          "✅ Добавлено: <b>{name}</b> — {qty} шт",
        "cart_title":     "🛒 <b>Ваш заказ:</b>",
        "cart_line":      "  • {emoji} {name} — {qty} шт",
        "add_more":       "➕ Добавить ещё",
        "next":           "➡️ Далее",
        "ask_phone":      "📞 Отправьте ваш номер телефона:",
        "share_phone":    "📱 Отправить мой номер",
        "invalid_phone":  "❌ Неверный номер. Введите снова:",
        "ask_location":   "📍 Отправьте ваш адрес (геолокация или текстом):",
        "share_loc":      "📍 Отправить геолокацию",
        "confirm_title":  "📋 <b>Подтвердите заказ:</b>",
        "confirm_phone":  "📞 Телефон: <code>{phone}</code>",
        "confirm_loc":    "📍 Адрес: {loc}",
        "btn_confirm":    "✅ Подтвердить",
        "btn_cancel":     "❌ Отмена",
        "order_sent":     "🎉 <b>Заказ №{order_id} принят!</b>\nОператор свяжется с вами в ближайшее время.",
        "cancelled":      "❌ Заказ отменён.",
        "new_order":      "🛒 Новый заказ",
        "change_lang":    "🌐 Сменить язык",
        "reply_sent":     "✅ Ответ отправлен клиенту.",
        "reply_fail":     "❌ Не удалось отправить ответ.",
    },
}
 
# ──────────────────────────────────────────────
#  Bot & Dispatcher
# ──────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
 
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp  = Dispatcher(storage=MemoryStorage())
 
# Буюртма рақамини сақлаш учун оддий счётчик
order_counter = 0
 
def next_order_id() -> int:
    global order_counter
    order_counter += 1
    return order_counter
 
 
# ──────────────────────────────────────────────
#  FSM States
# ──────────────────────────────────────────────
class S(StatesGroup):
    lang        = State()   # тил танлаш
    product     = State()   # маҳсулот танлаш
    quantity    = State()   # миқдор киритиш
    phone       = State()   # телефон
    location    = State()   # манзил
    confirm     = State()   # тасдиқлаш
 
 
# ──────────────────────────────────────────────
#  Keyboard helpers
# ──────────────────────────────────────────────
def kb_lang():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇺🇿 O'zbek",  callback_data="lang_uz"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
    ]])
 
 
def kb_main(lang: str):
    t = T[lang]
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t["new_order"])],
            [KeyboardButton(text=t["change_lang"])],
        ],
        resize_keyboard=True,
    )
 
 
def kb_products(lang: str):
    rows = []
    for pid, p in PRODUCTS.items():
        rows.append([InlineKeyboardButton(
            text=f"{p['emoji']} {p[lang]}",
            callback_data=f"p_{pid}",
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)
 
 
def kb_after_add(lang: str):
    t = T[lang]
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t["add_more"], callback_data="add_more"),
        InlineKeyboardButton(text=t["next"],     callback_data="go_next"),
    ]])
 
 
def kb_phone(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=T[lang]["share_phone"], request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True,
    )
 
 
def kb_location(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=T[lang]["share_loc"], request_location=True)]],
        resize_keyboard=True, one_time_keyboard=True,
    )
 
 
def kb_confirm(lang: str):
    t = T[lang]
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t["btn_confirm"], callback_data="c_yes"),
        InlineKeyboardButton(text=t["btn_cancel"],  callback_data="c_no"),
    ]])
 
 
# ──────────────────────────────────────────────
#  Utility
# ──────────────────────────────────────────────
def cart_text(cart: dict, lang: str) -> str:
    t = T[lang]
    lines = [t["cart_title"]]
    for pid, qty in cart.items():
        p = PRODUCTS[pid]
        lines.append(t["cart_line"].format(emoji=p["emoji"], name=p[lang], qty=qty))
    return "\n".join(lines)
 
 
def summary_text(data: dict, lang: str) -> str:
    t       = T[lang]
    cart    = data.get("cart", {})
    phone   = data.get("phone", "—")
    lat     = data.get("lat")
    lon     = data.get("lon")
    loc_str = data.get("loc_text", "—")
 
    loc_display = (
        f"<a href='https://maps.google.com/?q={lat},{lon}'>"
        f"{lat:.5f}, {lon:.5f}</a>"
        if lat else loc_str
    )
 
    lines = [
        t["confirm_title"],
        "",
        cart_text(cart, lang),
        "",
        t["confirm_phone"].format(phone=phone),
        t["confirm_loc"].format(loc=loc_display),
    ]
    return "\n".join(lines)
 
 
def admin_text(data: dict, user, order_id: int) -> str:
    cart    = data.get("cart", {})
    phone   = data.get("phone", "—")
    lang    = data.get("lang", "uz")
    lat     = data.get("lat")
    lon     = data.get("lon")
    loc_str = data.get("loc_text", "—")
    uname   = f"@{user.username}" if user.username else f"ID:{user.id}"
    full    = user.full_name or "—"
 
    loc_line = (
        f"<a href='https://maps.google.com/?q={lat},{lon}'>📍 Xaritada ko'rish</a>"
        if lat else f"📍 {loc_str}"
    )
 
    items = "\n".join(
        f"  • {PRODUCTS[pid]['emoji']} {PRODUCTS[pid]['uz']} — {qty} та"
        for pid, qty in cart.items()
    )
 
    return (
        f"🆕 <b>БУЮРТМА №{order_id}</b>\n\n"
        f"👤 {full}  ({uname})\n"
        f"📞 <code>{phone}</code>\n"
        f"{loc_line}\n\n"
        f"🛒 <b>Товарлар:</b>\n{items}\n\n"
        f"💬 Жавоб бериш учун: /reply_{order_id}_{user.id}"
    )
 
 
# ──────────────────────────────────────────────
#  /start
# ──────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    await state.set_state(S.lang)
    await msg.answer(
        "🛒 <b>СамМой маҳсулотлари</b>\n\n"
        "Tilni tanlang / Выберите язык:",
        reply_markup=kb_lang(),
    )
 
 
# ──────────────────────────────────────────────
#  Тил танлаш
# ──────────────────────────────────────────────
@dp.callback_query(F.data.in_({"lang_uz", "lang_ru"}), S.lang)
async def cb_lang(call: CallbackQuery, state: FSMContext):
    lang = "uz" if call.data == "lang_uz" else "ru"
    await state.update_data(lang=lang, cart={})
    t = T[lang]
    await call.message.edit_text("✅")
    await call.message.answer(t["welcome"], reply_markup=kb_main(lang))
    await state.set_state(None)
    await call.answer()
 
 
# ──────────────────────────────────────────────
#  Тилни ўзгартириш (менюдан)
# ──────────────────────────────────────────────
@dp.message(F.text.in_({T["uz"]["change_lang"], T["ru"]["change_lang"]}))
async def do_change_lang(msg: Message, state: FSMContext):
    await state.set_state(S.lang)
    await msg.answer("Tilni tanlang / Выберите язык:", reply_markup=kb_lang())
 
 
# ──────────────────────────────────────────────
#  Янги буюртма — маҳсулот танлаш
# ──────────────────────────────────────────────
@dp.message(F.text.in_({T["uz"]["new_order"], T["ru"]["new_order"]}))
async def new_order(msg: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.update_data(cart={}, cur_pid=None)
    await state.set_state(S.product)
    await msg.answer(T[lang]["choose_product"], reply_markup=kb_products(lang))
 
 
# ──────────────────────────────────────────────
#  Маҳсулот танланди → миқдор сўраш
# ──────────────────────────────────────────────
@dp.callback_query(F.data.startswith("p_"), S.product)
async def cb_product(call: CallbackQuery, state: FSMContext):
    pid  = call.data[2:]
    data = await state.get_data()
    lang = data.get("lang", "uz")
    p    = PRODUCTS.get(pid)
    if not p:
        await call.answer()
        return
    await state.update_data(cur_pid=pid)
    await state.set_state(S.quantity)
    await call.message.edit_text(
        f"{p['emoji']} <b>{p[lang]}</b>\n\n{T[lang]['enter_qty']}"
    )
    await call.answer()
 
 
# ──────────────────────────────────────────────
#  Миқдор киритилди
# ──────────────────────────────────────────────
@dp.message(S.quantity, F.text)
async def got_qty(msg: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    cart = data.get("cart", {})
    pid  = data.get("cur_pid")
    t    = T[lang]
 
    text = msg.text.strip()
    if not text.isdigit() or not (1 <= int(text) <= 999):
        await msg.answer(t["qty_error"])
        return
 
    qty       = int(text)
    cart[pid] = cart.get(pid, 0) + qty          # устига қўшади
    await state.update_data(cart=cart)
 
    p        = PRODUCTS[pid]
    added_msg = t["added"].format(name=p[lang], qty=qty)
    summary   = cart_text(cart, lang)
 
    await msg.answer(
        f"{added_msg}\n\n{summary}",
        reply_markup=kb_after_add(lang),
    )
    await state.set_state(S.product)              # кейинги маҳсулотga tayyor
 
 
# ──────────────────────────────────────────────
#  Яна қўшиш / Кейинги
# ──────────────────────────────────────────────
@dp.callback_query(F.data == "add_more", S.product)
async def cb_add_more(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await call.message.edit_text(T[lang]["choose_product"], reply_markup=kb_products(lang))
    await call.answer()
 
 
@dp.callback_query(F.data == "go_next", S.product)
async def cb_go_next(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.set_state(S.phone)
    await call.message.edit_text(T[lang]["ask_phone"])
    await call.message.answer("👇", reply_markup=kb_phone(lang))
    await call.answer()
 
 
# ──────────────────────────────────────────────
#  Телефон — контакт тугмаси
# ──────────────────────────────────────────────
@dp.message(S.phone, F.contact)
async def got_contact(msg: Message, state: FSMContext):
    phone = msg.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    await _save_phone(msg, state, phone)
 
 
# Телефон — қўлда матн
@dp.message(S.phone, F.text)
async def got_phone_text(msg: Message, state: FSMContext):
    data  = await state.get_data()
    lang  = data.get("lang", "uz")
    phone = msg.text.strip()
    d     = phone.replace("+", "").replace(" ", "").replace("-", "")
    if not d.isdigit() or len(d) < 9:
        await msg.answer(T[lang]["invalid_phone"], reply_markup=kb_phone(lang))
        return
    await _save_phone(msg, state, phone)
 
 
async def _save_phone(msg: Message, state: FSMContext, phone: str):
    await state.update_data(phone=phone)
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.set_state(S.location)
    await msg.answer(
        f"✅ <code>{phone}</code>\n\n{T[lang]['ask_location']}",
        reply_markup=kb_location(lang),
    )
 
 
# ──────────────────────────────────────────────
#  Локация — геолокация
# ──────────────────────────────────────────────
@dp.message(S.location, F.location)
async def got_location(msg: Message, state: FSMContext):
    await state.update_data(
        lat=msg.location.latitude,
        lon=msg.location.longitude,
        loc_text=None,
    )
    await _show_confirm(msg, state)
 
 
# Локация — матн
@dp.message(S.location, F.text)
async def got_location_text(msg: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    # Тугма матнини ўтказиб юбориш
    if msg.text in {T["uz"]["share_loc"], T["ru"]["share_loc"]}:
        return
    await state.update_data(lat=None, lon=None, loc_text=msg.text.strip())
    await _show_confirm(msg, state)
 
 
async def _show_confirm(msg: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.set_state(S.confirm)
    await msg.answer(summary_text(data, lang), reply_markup=kb_confirm(lang))
 
 
# ──────────────────────────────────────────────
#  Тасдиқлаш
# ──────────────────────────────────────────────
@dp.callback_query(F.data == "c_yes", S.confirm)
async def cb_confirm(call: CallbackQuery, state: FSMContext):
    data     = await state.get_data()
    lang     = data.get("lang", "uz")
    order_id = next_order_id()
 
    # 1) Adminга хабар юбор
    try:
        await bot.send_message(
            ADMIN_CHAT_ID,
            admin_text(data, call.from_user, order_id),
            disable_web_page_preview=True,
        )
        # Геолокация бор бўлса — картани ҳам юбор
        if data.get("lat"):
            await bot.send_location(ADMIN_CHAT_ID, data["lat"], data["lon"])
    except Exception as e:
        logger.error(f"Admin xabar xatosi: {e}")
 
    # 2) Фойдаланувчига тасдиқ
    await call.message.edit_reply_markup()
    await call.message.answer(
        T[lang]["order_sent"].format(order_id=order_id),
        reply_markup=kb_main(lang),
    )
 
    # State тозалаш (тилни сақлаш)
    await state.update_data(cart={}, phone=None, lat=None, lon=None, loc_text=None)
    await state.set_state(None)
    await call.answer()
 
 
@dp.callback_query(F.data == "c_no", S.confirm)
async def cb_cancel_order(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await call.message.edit_reply_markup()
    await call.message.answer(T[lang]["cancelled"], reply_markup=kb_main(lang))
    await state.set_state(None)
    await call.answer()
 
 
# ──────────────────────────────────────────────
#  Admin жавоби: /reply_<order_id>_<user_id>  <матн>
#  Мисол: /reply_5_987654321 Буюртмангиз йўлда!
# ──────────────────────────────────────────────
@dp.message(F.text.regexp(r"^/reply_(\d+)_(\d+)\s+(.+)$"))
async def admin_reply(msg: Message):
    if msg.from_user.id != ADMIN_CHAT_ID:
        return                              # фақат admin
 
    import re
    m       = re.match(r"^/reply_(\d+)_(\d+)\s+(.+)$", msg.text, re.DOTALL)
    order_id = m.group(1)
    user_id  = int(m.group(2))
    text     = m.group(3).strip()
 
    try:
        await bot.send_message(
            user_id,
            f"📬 <b>Буюртма №{order_id} бўйича оператор жавоби:</b>\n\n{text}",
        )
        await msg.answer(T["uz"]["reply_sent"])
    except Exception as e:
        logger.error(f"Reply xatosi: {e}")
        await msg.answer(T["uz"]["reply_fail"])
 
 
# ──────────────────────────────────────────────
#  Асосий функция
# ──────────────────────────────────────────────
async def main():
    logger.info("СамМой боти ишга тушди ✅")
    await dp.start_polling(bot)
 
 
if __name__ == "__main__":
    asyncio.run(main())
