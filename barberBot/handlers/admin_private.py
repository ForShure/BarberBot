from datetime import datetime, timedelta
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery

# Импорты настроек и сервисов
from config import ADMIN_ID, TIMEZONE
from services import master_service, appointment_service
from services.master_service import get_weekends_days, toggle_day_off

from handlers.keyboards import (
    create_admin_keyboard,
    create_main_keyboard,
    create_delete_keyboard,
    create_admin_master_keyboard,
    get_master_schedule_keyboard,
)

# Создаем отдельный роутер для админа
admin_router = Router()

# 🔥 ГЛАВНАЯ ЗАЩИТА:
# Все хендлеры в этом файле сработают ТОЛЬКО если пишет ADMIN_ID.
# Нам больше не нужно писать F.from_user.id == ADMIN_ID в каждой строчке.
admin_router.message.filter(F.from_user.id == ADMIN_ID)
admin_router.callback_query.filter(F.from_user.id == ADMIN_ID)


# --- Хендлеры Админа ---

@admin_router.message(Command("admin"))
async def admin_start(message: types.Message):
    await message.answer("👨‍💼 The admin panel is active!", reply_markup=create_admin_keyboard())

# Вспомогательная функция (не хендлер, просто функция)
async def show_appointments_for_date(message: types.Message, target_date):
    appointments = await appointment_service.get_appointments_by_date(target_date)

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

@admin_router.message(F.text == "📅 Today's appointments")
async def admin_today(message: types.Message):
    today = datetime.now(TIMEZONE).date()
    await show_appointments_for_date(message, today)

@admin_router.message(F.text == "📅 Tomorrow's appointments")
async def admin_tomorrow(message: types.Message):
    tomorrow = datetime.now(TIMEZONE).date() + timedelta(days=1)
    await show_appointments_for_date(message, tomorrow)

@admin_router.message(F.text == "📅 Schedule")
async def admin_schedule(message: types.Message):
    masters = await master_service.get_all_masters()
    await message.answer("Choose a master:", reply_markup=create_admin_master_keyboard(masters))

@admin_router.message(F.text.contains("🔙 Logout"))
async def admin_exit(message: types.Message):
    await message.answer("Admin mode is disabled.", reply_markup=create_main_keyboard(message.from_user.id))

# --- Callback-и Админа ---
@admin_router.callback_query(F.data.startswith("sched_"))
async def open_master_schedule(callback: CallbackQuery):
    await callback.answer()
    master_id = callback.data.split("_")[1]
    day_off = await get_weekends_days(master_id)
    await callback.message.edit_text(
        "📅 Master's schedule. Click on the date to change:",
        reply_markup=get_master_schedule_keyboard(master_id, day_off)
    )

@admin_router.callback_query(F.data.startswith("toggle_"))
async def toggle_day(callback: CallbackQuery):
    await callback.answer()
    _, master_id, date_str = callback.data.split("_")
    await toggle_day_off(master_id, date_str)
    day_off = await get_weekends_days(master_id)
    await callback.message.edit_reply_markup(reply_markup=get_master_schedule_keyboard(master_id, day_off))