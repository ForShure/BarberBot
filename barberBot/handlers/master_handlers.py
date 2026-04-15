from aiogram import Router, F, types
from filters.is_master import IsMaster

from datetime import datetime, timedelta
from config import TIMEZONE
from aiogram.filters import Command
from services import appointment_service

from handlers.keyboards import (
    create_master_keyboard,
    create_main_keyboard,
    create_delete_keyboard,
)

master_router = Router()

master_router.message.filter(IsMaster())
master_router.callback_query.filter(IsMaster())

@master_router.message(Command("master"))
async def admin_start(message: types.Message):
    await message.answer("✂️ The master's office is active!", reply_markup=create_master_keyboard(message.from_user.id))

# Вспомогательная функция (не хендлер, просто функция)
async def show_appointments_for_date(message: types.Message, target_date, telegram_id):
    appointments = await appointment_service.get_master_appointments_by_date(target_date, telegram_id)

    if not appointments:
        await message.answer("📭 There are no entries.")
        return

    for app in appointments:
        time_str = app.time.strftime("%H:%M")
        client_name = app.client_name or (app.user.username if app.user else "Client from the website")
        client_phone = app.phone or (app.user.phone if app.user else "No number")

        text = (
            f"🕒 <b>{time_str}</b> — {app.service.name}\n"
            f"👤 {client_name}\n"
            f"📞 <code>{client_phone}</code>\n"
            f"✂️ Master: {app.master.name}\n"
            f"➖➖➖➖➖➖➖➖"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=create_delete_keyboard(app.id))

@master_router.message(F.text == "📅 Today's entries")
async def admin_today(message: types.Message):
    today = datetime.now(TIMEZONE).date()
    await show_appointments_for_date(message, today, message.from_user.id)

@master_router.message(F.text == "📅 Entries for tomorrow")
async def admin_tomorrow(message: types.Message):
    tomorrow = datetime.now(TIMEZONE).date() + timedelta(days=1)
    await show_appointments_for_date(message, tomorrow, message.from_user.id)

@master_router.message(F.text.contains("🔙 Logout"))
async def admin_exit(message: types.Message):
    await message.answer("Master mode is disabled.", reply_markup=create_main_keyboard(message.from_user.id))