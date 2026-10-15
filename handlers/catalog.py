from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

router = Router()

# База товаров
PRODUCTS = [
    {"id": 1, "name": "Пакет с петлевой ручкой", "price": 150, "desc": "Прочный пакет 40х50 см"},
    {"id": 2, "name": "Пакет Майка", "price": 80, "desc": "Пакет майка 30х50 см"},
    {"id": 3, "name": "Курьерский пакет", "price": 120, "desc": "Влагозащитный пакет с клапаном"}
]

# Временное хранилище корзин пользователей: { user_id: { product_id: count } }
USER_CARTS = {}

# Вспомогательная функция для генерации текста и клавиатуры корзины
def get_cart_details(user_id: int):
    cart = USER_CARTS.get(user_id, {})
    if not cart:
        return "🛒 <b>Ваша корзина пуста.</b>", None

    text = "🛒 <b>Ваша корзина:</b>\n\n"
    total = 0
    inline_keyboard = []

    for p_id, count in cart.items():
        product = next((p for p in PRODUCTS if p["id"] == p_id), None)
        if product:
            subtotal = product["price"] * count
            total += subtotal
            text += f"• <b>{product['name']}</b>: {count} шт. × {product['price']} грн = {subtotal} грн\n"
            
            # Кнопки изменения количества для каждого товара
            inline_keyboard.append([
                InlineKeyboardButton(text=f"➖ 1", callback_data=f"remove_{p_id}"),
                InlineKeyboardButton(text=f"{product['name'][:15]}...", callback_data="ignore"),
                InlineKeyboardButton(text=f"➕ 1", callback_data=f"add_{p_id}")
            ])

    text += f"\n💰 <b>Итого к оплате: {total} грн</b>"
    
    # Кнопка оформления и очистки
    inline_keyboard.append([
        InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout"),
        InlineKeyboardButton(text="🗑 Очистить", callback_data="clear_cart")
    ])

    return text, InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


# Показ каталога
@router.message(F.text == "🛒 Каталог товаров")
async def show_catalog(message: types.Message):
    await message.answer("📋 <b>Наш каталог товаров:</b>\nВыберите интересующую позицию:", parse_mode="HTML")
    
    for item in PRODUCTS:
        p_id = item['id']
        p_name = item['name']
        p_price = item['price']
        p_desc = item['desc']
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"Добавить в корзину ({p_price} грн)", callback_data=f"buy_{p_id}")]
        ])
        
        await message.answer(
            f"📦 <b>{p_name}</b>\nОписание: {p_desc}\nЦена: {p_price} грн",
            reply_markup=kb,
            parse_mode="HTML"
        )


# Добавление товара в корзину
@router.callback_query(F.data.startswith("buy_"))
async def add_to_cart(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    if user_id not in USER_CARTS:
        USER_CARTS[user_id] = {}
        
    USER_CARTS[user_id][product_id] = USER_CARTS[user_id].get(product_id, 0) + 1
    
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    await callback.answer(f"✅ '{product['name']}' добавлен в корзину!", show_alert=False)


# Увеличение количества товара
@router.callback_query(F.data.startswith("add_"))
async def increase_item(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    if user_id in USER_CARTS and product_id in USER_CARTS[user_id]:
        USER_CARTS[user_id][product_id] += 1
        
    text, kb = get_cart_details(user_id)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


# Уменьшение количества товара
@router.callback_query(F.data.startswith("remove_"))
async def decrease_item(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    if user_id in USER_CARTS and product_id in USER_CARTS[user_id]:
        USER_CARTS[user_id][product_id] -= 1
        if USER_CARTS[user_id][product_id] <= 0:
            del USER_CARTS[user_id][product_id]
            
    text, kb = get_cart_details(user_id)
    if kb:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.edit_text("🛒 <b>Ваша корзина пуста.</b>", parse_mode="HTML")
    await callback.answer()


# Очистка корзины
@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    USER_CARTS[user_id] = {}
    await callback.message.edit_text("🛒 <b>Корзина очищена.</b>", parse_mode="HTML")
    await callback.answer()


# Заглушка клика на название товара в инлайне
@router.callback_query(F.data == "ignore")
async def ignore_click(callback: CallbackQuery):
    await callback.answer()