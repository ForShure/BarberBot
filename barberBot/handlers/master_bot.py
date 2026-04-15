import json
import random

from aiogram import Router, F, types
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, FSInputFile, Message, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID, PAYMENT_TOKEN
from services import user_service, master_service, appointment_service
from services.master_service import get_weekends_days, get_master_by_id, get_service_by_id, get_salon_config
from services.google_sheets_service import save_to_google_sheet
from services.appointment_service import save_certificate, get_user_certificates
from states import ProfileStates


from handlers.keyboards import (
    create_masters_keyboard,
    create_services_keyboard,
    create_data_keyboard,
    create_time_keyboard,
    create_contact_keyboard,
    create_main_keyboard,
    create_delete_keyboard,
    create_keyboard_return_master,
    create_cert_keyboard,
)

user_router = Router()

# --- Хендлеры Пользователя ---

@user_router.message(Command("start"))
async def start(message: types.Message, command: CommandObject, state: FSMContext):
    await user_service.register_user(message.chat.id, message.from_user.username)

    config = await get_salon_config()
    if config and config.welcome_text:
        welcome_message = config.welcome_text
    else:
        welcome_message = "Welcome! Select an action:"
    user = await appointment_service.get_user_by_chat_id(message.chat.id)

    if not user.phone:
        await message.answer("📱 We need your phone number to make an appointment.:", reply_markup=create_contact_keyboard())


        await state.update_data(is_registration=True)

        await state.set_state(ProfileStates.waiting_for_new_phone)
        return

    if command.args:
        services = await appointment_service.get_services()
        await message.answer("🌐 Selecting a service:", reply_markup=create_services_keyboard(services, command.args))
    else:
        await message.answer(
            welcome_message,
            reply_markup=create_main_keyboard(message.from_user.id)
        )


@user_router.message(F.contact)
async def handle_contact(message: types.Message):
    await appointment_service.save_user_phone(message.chat.id, message.contact.phone_number)
    await message.answer("✅ The number has been saved.!", reply_markup=create_main_keyboard(message.from_user.id))

@user_router.message(F.text == "Master")
async def show_masters(message: types.Message):
    masters = await master_service.get_all_masters()
    await message.answer("Our masters:", reply_markup=create_masters_keyboard(masters))

@user_router.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    raw_data = message.web_app_data.data
    data = json.loads(raw_data)

    master_id = data.get('master_id')
    service_id = data.get('service_id')
    date_val = data.get('date')
    time_val = data.get('time')

    # 1. ОБЯЗАТЕЛЬНО ДОБАВЛЯЕМ await!
    master_obj = await get_master_by_id(master_id)
    service_obj = await get_service_by_id(service_id)

    # 2. ДОСТАЕМ ИМЕНА ИЗ ОБЪЕКТОВ (предполагая, что в БД поле называется name)
    # Если объекта почему-то нет, пишем просто ID, чтобы не было ошибки
    master_name = master_obj.name if master_obj else f"ID {master_id}"
    service_name = service_obj.name if service_obj else f"ID {service_id}"

    # 3. Достаем Telegram ID клиента
    user_telegram_id = message.from_user.id

    # 4. Сохраняем в базу (тут ты передаешь ID, это правильно!)
    app = await appointment_service.create_appointment(
        user_telegram_id, master_id, service_id, date_val, time_val
    )
    if app:
        client_phone = app.user.phone if app.user else "Не указан"

        await save_to_google_sheet(
            date_val, time_val, message.from_user.full_name,
            client_phone, service_name, master_name,
            app.service.price
        )
    # 5. Красивый текст для клиента с ИМЕНАМИ
    text = (
        f"🎉 <b>Successful recording!</b>\n\n"
        f"✂️ Master: {master_name}\n"
        f"📅 Service: {service_name}\n"
        f"📅 Date: {date_val}\n"
        f"⏰ Time: {time_val}\n\n"
        f"Waiting for you!"
    )
    await message.answer(text, parse_mode="HTML")


@user_router.message(F.text == "My appointments")
async def show_notes(message: types.Message):
    appointments = await appointment_service.get_user_appointments(message.from_user.id)
    if not appointments:
        await message.answer("You have no active posts.")
        return

    for app in appointments:
        text = (f"📅 {app.date.strftime('%d.%m.%Y')} в {app.time.strftime('%H:%M')}\n"
                f"✂️ {app.master.name} | {app.service.name}")
        await message.answer(text, reply_markup=create_delete_keyboard(app.id))


@user_router.message(F.text == "Профиль")
async def show_profile(message: types.Message):
    user = await appointment_service.get_user_by_chat_id(message.chat.id)
    if user:
        # Сначала убедились, что юзер есть, и только потом достаем телефон
        phone = user.phone if user.phone else "Не указан"

        # Формируем текст ОДИН раз, подставляя переменную phone
        text = f"👤 <b>Your profile:</b>\n📱 Phone number: {phone}"

        await message.answer(text, parse_mode="HTML")

# --- Callback-и Пользователя ---

@user_router.callback_query(F.data.startswith('master_'))
async def select_master(callback: CallbackQuery):
    master_id = callback.data.split('_')[1]

    master = await get_master_by_id(master_id)
    keyboard = create_keyboard_return_master(master_id)
    photo = FSInputFile(master.photo.path)

    await callback.message.delete()
    await callback.message.answer_photo(photo, caption=master.description, reply_markup=keyboard)
    await callback.answer()

@user_router.callback_query(F.data.startswith('service_'))
async def select_service(callback: CallbackQuery):
    _, service_id, master_id = callback.data.split('_')
    day_off = await get_weekends_days(master_id)

    await callback.message.edit_text("Select date:", reply_markup=create_data_keyboard(master_id, service_id, day_off))

@user_router.callback_query(F.data.startswith('data_'))
async def select_date(callback: CallbackQuery):
    _, date_val, master_id, service_id = callback.data.split('_')
    taken_slots = await appointment_service.get_taken_slots(master_id, date_val)

    await callback.message.edit_text("Select time:", reply_markup=create_time_keyboard(master_id, service_id, date_val, taken_slots))

@user_router.callback_query(F.data.startswith('time_'))
async def handle_time(callback: CallbackQuery):
    parts = callback.data.split('_')
    time_val = parts[1]
    date_val = parts[2]
    master_id = parts[3]
    service_id = parts[4]

    app = await appointment_service.create_appointment(
        callback.from_user.id, master_id, service_id, date_val, time_val
    )

    if app:
        await callback.message.edit_text(
            f"✅ <b>YOU ARE SIGNED UP!</b>\n📅 {date_val} at {time_val}\n✂️ master: {app.master.name}",
            parse_mode="HTML"
        )

        client_phone = app.user.phone if app.user else "Not specified"

        await save_to_google_sheet(
            date_val, time_val, callback.from_user.full_name,
            client_phone, app.service.name, app.master.name,
            app.service.price
        )
        try:
            await callback.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🚀 <b>NEW POST (BOT)!</b>\n👤 @{callback.from_user.username}\n📅 {date_val} {time_val}",
                parse_mode="HTML"  # 👈 Волшебная таблетка
            )
        except:
            pass
    else:
        await callback.answer("Error! The time may already be taken.", show_alert=True)


@user_router.callback_query(F.data.startswith('del_'))
async def handle_delete(callback: CallbackQuery):
    app_id = callback.data.split('_')[1]
    app = await appointment_service.get_appointments_by_id(app_id)

    if app:
        # 1. Сохраняем нужные данные в переменные ДО того, как удалим запись
        master_name = app.master.name
        app_date = app.date
        app_time = app.time
        client_chat_id = app.user.chat_id if app.user else None # Защита от записей с сайта (где нет юзера ТГ)

        # 2. Удаляем из базы
        await appointment_service.delete_appointment(app_id)

        # 3. 🚦 РАЗВИЛКА: Кто нажал на кнопку?
        if callback.from_user.id == ADMIN_ID:
            # СЦЕНАРИЙ А: Кнопку нажал АДМИН
            if client_chat_id: # Если клиент из Телеграма, а не с улицы/сайта
                client_text = f"😔 <b>Your appointment has been cancelled!</b>\nUnfortunately, your appointment with {master_name} on {app_date} at {app_time} has been cancelled."
                try:
                    # Отправляем сообщение КЛИЕНТУ
                    await callback.bot.send_message(chat_id=client_chat_id, text=client_text, parse_mode="HTML")
                except:
                    pass # На случай, если клиент заблокировал бота
        else:
            # СЦЕНАРИЙ Б: Кнопку нажал КЛИЕНТ (твой старый код)
            user_identifier = f"@{callback.from_user.username}" if callback.from_user.username else callback.from_user.full_name
            admin_text = f"❌ <b>CANCEL APPOINTMENT (CLIENT)!</b>\n👤 {user_identifier}\n✂️ Master: {master_name}\n📅 {app_date} at {app_time}"
            try:
                # Отправляем сообщение АДМИНУ
                await callback.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="HTML")
            except:
                pass

    # Эти две строчки выполнятся в любом случае
    await callback.message.delete()
    await callback.answer("The appointment has been successfully cancelled.", show_alert=True)


@user_router.callback_query(F.data == "back_to_masters")
async def back_to_masters(callback: CallbackQuery):
    masters = await master_service.get_all_masters()

    # 1. Удаляем фотку
    await callback.message.delete()

    # 2. Отправляем НОВОЕ текстовое сообщение с кнопками
    await callback.message.answer("Choose a master:", reply_markup=create_masters_keyboard(masters))

    # 3. Гасим часики
    await callback.answer()

@user_router.callback_query(F.data.startswith('book_master_'))
async def book_master(callback: CallbackQuery):
    master_id = callback.data.split('_')[2]

    services = await appointment_service.get_services()

    await callback.message.delete()
    await callback.message.answer(text=f"Select a service:", reply_markup=create_services_keyboard(services, master_id))
    await callback.answer()

@user_router.callback_query(F.data == "change_phone")
async def change_phone(callback: CallbackQuery, state: FSMContext):

    await callback.message.answer("📱 Please reply to this message with your new phone number.:")

    await state.set_state(ProfileStates.waiting_for_new_phone)

    await callback.answer()


@user_router.message(ProfileStates.waiting_for_new_phone)
async def save_new_phone(message: types.Message, state: FSMContext):
    new_phone = message.text
    await appointment_service.save_user_phone(message.chat.id, new_phone)
    await message.answer(f"✅ Great! Your new number <b>{new_phone}</b> has been saved successfully.", parse_mode="HTML")

    # 🔥 ЧИТАЕМ ПАМЯТЬ БОТА ПЕРЕД ОЧИСТКОЙ:
    data = await state.get_data()

    await state.clear()  # Очищаем ждуна и память

    # ПРОВЕРЯЕМ ЗАПИСКУ:
    if data.get("is_registration"):
        await message.answer("✂️ Welcome! Select an action:",
                             reply_markup=create_main_keyboard(message.from_user.id))
    else:
        await message.answer("We return you to the menu:", reply_markup=create_main_keyboard(message.from_user.id))

@user_router.message(F.text == "🎁 Certificates")
async def show_certificates(message: types.Message):
    await message.answer(
        text="These are certificates for the purchase of various services and cosmetics in our barbershop. 💈",
        reply_markup=create_cert_keyboard()
    )

@user_router.callback_query(F.data == "buy_cert_500")
async def send_invoice(callback: CallbackQuery):
    if not PAYMENT_TOKEN:
        await callback.message.answer("Error: Payment token not found.")
        return
    promo_code = f"BARBER-{random.randint(100000, 999999)}"
    prices = [LabeledPrice(label="Prepayment", amount=50000)]
    await callback.message.answer_invoice(
        title="Gift certificate",
        description="Payment for the service",
        payload=promo_code,
        provider_token=PAYMENT_TOKEN,
        currency="UAH",
        prices=prices,
        start_parameter="test-payment"
    )
    await callback.answer()

@user_router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@user_router.message(F.successful_payment)
async def successful_payment_handler(message: types.Message):
    payment_info = message.successful_payment
    amount = payment_info.total_amount // 100
    user_id = message.from_user.id

    promo_code = payment_info.invoice_payload
    certificate, created = await save_certificate(user_id, promo_code, amount)
    if not created:
        return
    text = (
        f"🎉 <b>Payment successfully received!</b>\n"
        f"You purchased a certificate for {amount} {payment_info.currency}.\n\n"
        f"🎁 Your unique code: <code>{promo_code}</code>\n"
        f"Show it to the administrator upon your visit!"
    )

    await message.answer(text, parse_mode="HTML")

@user_router.message(Command("my_cert"))
async def my_cert(message: types.Message):
    user_id = message.from_user.id
    cert = await get_user_certificates(user_id)

    answer_text = (
        f"<b>🎟 Your active certificates:</b>\n\n"
    )
    if cert:
        for c in cert:
            answer_text += f"🎁 Code: <code>{c.promo}</code> — {c.amount} UAH\n"
        await message.answer(answer_text, parse_mode="HTML")
    else:
        await message.answer(f"You don't have any active certificates yet.")




