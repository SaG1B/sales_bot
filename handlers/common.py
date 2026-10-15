from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from handlers.catalog import get_cart_details

router = Router()

BTN_CATALOG = "🛒 Каталог товаров"
BTN_CART = "🛒 Корзина"
BTN_ORDERS = "📦 Мои заказы"
BTN_SUPPORT = "📞 Поддержка"

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_CATALOG), KeyboardButton(text=BTN_CART)],
        [KeyboardButton(text=BTN_ORDERS), KeyboardButton(text=BTN_SUPPORT)]
    ],
    resize_keyboard=True
)

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.full_name}! Добро пожаловать в наш магазин.",
        reply_markup=main_keyboard
    )

# Показ корзины по кнопке из нижнего меню
@router.message(F.text == BTN_CART)
@router.message(F.text.lower().contains("корзин"))
async def show_cart_handler(message: types.Message):
    text, kb = get_cart_details(message.from_user.id)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

# Обработка кнопки Поддержка
@router.message(F.text == BTN_SUPPORT)
@router.message(F.text.lower().contains("поддержка"))
async def cmd_support(message: types.Message):
    await message.answer(
        "💬 <b>Служба поддержки Eventus Group</b>\n\n"
        "По всем вопросам заказа, просчета индивидуальных размеров и оптовых поставок свяжитесь с менеджером:\n"
        "👨‍💼 Telegram: @manager_username\n"
        "📞 Телефон: +380 (XX) XXX-XX-XX",
        parse_mode="HTML"
    )

# Обработка кнопки Мои заказы
@router.message(F.text == BTN_ORDERS)
@router.message(F.text.lower().contains("заказ"))
async def cmd_orders(message: types.Message):
    await message.answer(
        "📦 <b>История заказов:</b>\n\n"
        "У вас пока нет активных заказов.\n"
        "Выберите товар из 🛒 <b>Каталога товаров</b>, чтобы сделать первый заказ!",
        parse_mode="HTML"
    )