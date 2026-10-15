from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from handlers.catalog import USER_CARTS, PRODUCTS

router = Router()

# Укажи здесь свой цифровой Telegram ID (получи его у бота @userinfobot)
ADMIN_ID = 123456789


class OrderForm(StatesGroup):
    full_name = State()   # Ожидание ФИО
    phone = State()       # Ожидание телефона
    delivery = State()    # Ожидание города и отделения Новой Почты


# Запуск процесса оформления по кнопке "Оформить заказ" из корзины
@router.callback_query(F.data == "checkout")
async def start_checkout(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    cart = USER_CARTS.get(user_id, {})
    
    if not cart:
        await callback.answer("Ваша корзина пуста!", show_alert=True)
        return
    
    await state.set_state(OrderForm.full_name)
    await callback.message.answer(
        "📝 <b>Оформление заказа</b>\n\n"
        "Шаг 1 из 3: Введите ваше <b>ФИО получателя</b> (например: Иванов Иван Иванович):",
        parse_mode="HTML"
    )
    await callback.answer()


# Шаг 1: Получаем ФИО и запрашиваем Телефон
@router.message(OrderForm.full_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поделиться контактом", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await state.set_state(OrderForm.phone)
    await message.answer(
        "Шаг 2 из 3: Введите ваш <b>номер телефона</b> или нажмите кнопку ниже:",
        reply_markup=kb,
        parse_mode="HTML"
    )


# Шаг 2: Получаем Телефон и запрашиваем Адрес/Отделение
@router.message(OrderForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone_number = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone_number)
    
    await state.set_state(OrderForm.delivery)
    await message.answer(
        "Шаг 3 из 3: Укажите <b>Город и № отделения Новой Почты</b> (например: Днепр, отделение №12):",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )


# Шаг 3: Финал — формирование заказа, подтверждение клиенту и отправка менеджеру
@router.message(OrderForm.delivery)
async def process_delivery(message: types.Message, state: FSMContext):
    await state.update_data(delivery=message.text)
    user_data = await state.get_data()
    
    user_id = message.from_user.id
    cart = USER_CARTS.get(user_id, {})
    
    # Считаем товары и итоговую сумму
    order_items = []
    total_sum = 0
    for p_id, count in cart.items():
        product = next((p for p in PRODUCTS if p["id"] == p_id), None)
        if product:
            subtotal = product["price"] * count
            total_sum += subtotal
            order_items.append(f"• {product['name']} — {count} шт. ({subtotal} грн)")
            
    items_text = "\n".join(order_items)
    
    # 1. Формируем сообщение для покупателя
    order_summary = (
        f"🎉 <b>Спасибо! Ваш заказ принят.</b>\n\n"
        f"📋 <b>Состав заказа:</b>\n{items_text}\n\n"
        f"💰 <b>Сумма к оплате:</b> {total_sum} грн\n\n"
        f"👤 <b>Получатель:</b> {user_data['full_name']}\n"
        f"📞 <b>Телефон:</b> {user_data['phone']}\n"
        f"🚚 <b>Доставка:</b> {user_data['delivery']}\n\n"
        f"Менеджер свяжется с вами в ближайшее время!"
    )
    
    # Возвращаем клиенту главное меню
    from handlers.common import main_keyboard
    await message.answer(order_summary, reply_markup=main_keyboard, parse_mode="HTML")
    
    # 2. Формируем и отправляем уведомление менеджеру
    client_username = f"@{message.from_user.username}" if message.from_user.username else "не указан"
    admin_notification = (
        f"🚨 <b>НОВЫЙ ЗАКАЗ В МАГАЗИНЕ!</b>\n\n"
        f"👤 <b>Заказчик:</b> {user_data['full_name']} ({client_username})\n"
        f"📞 <b>Телефон:</b> {user_data['phone']}\n"
        f"🚚 <b>Адрес доставки:</b> {user_data['delivery']}\n\n"
        f"📦 <b>Состав заказа:</b>\n{items_text}\n\n"
        f"💰 <b>Итого к оплате:</b> {total_sum} грн"
    )
    
    try:
        # Отправка администратору по его цифровому ID
        await message.bot.send_message(chat_id=ADMIN_ID, text=admin_notification, parse_mode="HTML")
    except Exception as e:
        print(f"[ОШИБКА ОТПРАВКИ АДМИНУ]: {e}")

    # 3. Очищаем корзину и сбрасываем состояние
    USER_CARTS[user_id] = {}
    await state.clear()