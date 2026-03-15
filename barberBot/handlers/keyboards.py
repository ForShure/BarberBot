"""
keyboards.py

Этот файл отвечает за:
- создание inline-клавиатур (кнопки внутри сообщения)
- создание reply-клавиатур (нижняя клавиатура Telegram)

Структура:
1. Пользовательские клавиатуры
2. Админские клавиатуры
3. График мастеров
"""

import pytz
from datetime import datetime, timedelta

from aiogram.types import InlineKeyboardButton, KeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup


# 1. ПОЛЬЗОВАТЕЛЬСКИЕ КЛАВИАТУРЫ

# Выбор мастера
def create_masters_keyboard(masters):
    """
    Создаёт список мастеров.
    При нажатии отправляется callback: master_<id>
    """
    builder = InlineKeyboardBuilder()

    for master in masters:
        builder.button(
            text=master['name'],
            callback_data=f"master_{master['id']}"
        )

    builder.adjust(1)  # по одной кнопке в ряд
    return builder.as_markup()

# Выбор услуги
def create_services_keyboard(services, master_id):
    """
    Показывает список услуг выбранного мастера.
    callback: service_<service_id>_<master_id>
    """
    builder = InlineKeyboardBuilder()

    for service in services:
        builder.button(
            text=f"{service.name} ({service.price}₽)",
            callback_data=f"service_{service.id}_{master_id}"
        )

    builder.adjust(2)  # по 2 кнопки в ряд

    # Кнопка назад
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_masters"
        )
    )

    return builder.as_markup()

# Выбор даты
def create_data_keyboard(master_id, service_id, day_off):
    """
    Показывает ближайшие 7 дней.
    Не отображает дни, когда мастер не работает.
    callback: data_<YYYY-MM-DD>_<master_id>_<service_id>
    """
    builder = InlineKeyboardBuilder()
    current_time = datetime.now()

    for i in range(7):
        future_date = current_time + timedelta(days=i)

        display_date = future_date.strftime("%d.%m")
        callback_date = future_date.strftime("%Y-%m-%d")

        # Если день выходной — не показываем
        if callback_date in day_off:
            continue

        builder.button(
            text=display_date,
            callback_data=f"data_{callback_date}_{master_id}_{service_id}"
        )

    builder.adjust(3)  # по 3 даты в ряд

    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"back_to_services_{master_id}"
        )
    )

    return builder.as_markup()

# Выбор времени
def create_time_keyboard(master_id, service_id, date, occupied_times):
    """
    Показывает свободное время.
    Не отображает:
    - уже занятое время
    - прошедшие часы текущего дня
    callback: time_<HH:MM>_<date>_<master_id>_<service_id>
    """
    builder = InlineKeyboardBuilder()

    times = [
        "10:00", "11:00", "12:00", "13:00", "14:00",
        "15:00", "16:00", "17:00", "18:00", "19:00"
    ]

    timezone = pytz.timezone("Europe/Kiev")
    now = datetime.now(timezone)

    today_str = now.strftime("%Y-%m-%d")
    current_hour = now.hour

    for time in times:
        slot_hour = int(time.split(":")[0])

        # Если слот занят — пропускаем
        if time in occupied_times:
            continue

        # Если это сегодня и время уже прошло — пропускаем
        if date == today_str and slot_hour <= current_hour:
            continue

        builder.button(
            text=time,
            callback_data=f"time_{time}_{date}_{master_id}_{service_id}"
        )

    builder.adjust(4)  # по 4 кнопки в ряд

    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"back_to_dates_{master_id}_{service_id}"
        )
    )

    return builder.as_markup()

# Клавиатура запроса телефона
def create_contact_keyboard():
    """
    Просит пользователя отправить номер телефона.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Удаление записи
def create_delete_keyboard(appointment_id):
    """
    Кнопка удаления записи.
    callback: del_<appointment_id>
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text="❌ Удалить запись",
        callback_data=f"del_{appointment_id}"
    )

    builder.adjust(1)
    return builder.as_markup()

# Главное меню
def create_main_keyboard():
    """
    Главное меню пользователя.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Записаться онлайн", web_app=WebAppInfo(url="https://nonclamorous-nonavoidably-kamila.ngrok-free.dev/webapp/"))],
            [KeyboardButton(text="Мои записи")],
            [KeyboardButton(text="Профиль")],
        ],
        resize_keyboard=True
    )

# 2. АДМИНСКИЕ КЛАВИАТУРЫ
def create_admin_keyboard():
    """
    Главное меню администратора.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Записи на сегодня")],
            [KeyboardButton(text="📅 Записи на завтра")],
            [KeyboardButton(text="📅 График работы")],
            [KeyboardButton(text="🔙 Выйти")],
        ],
        resize_keyboard=True
    )

# 3. ГРАФИК РАБОТЫ МАСТЕРА
def get_master_schedule_keyboard(master_id, day_off_list):
    """
    Клавиатура для редактирования графика.
    Зеленый — работает
    Красный — выходной

    callback: toggle_<master_id>_<date>
    """
    builder = InlineKeyboardBuilder()
    current_time = datetime.now()

    for i in range(7):
        future_date = current_time + timedelta(days=i)

        display_date = future_date.strftime("%d.%m")
        callback_date = future_date.strftime("%Y-%m-%d")

        if callback_date in day_off_list:
            text = f"🟥 {display_date}"
        else:
            text = f"✅ {display_date}"

        builder.button(
            text=text,
            callback_data=f"toggle_{master_id}_{callback_date}"
        )

    builder.adjust(3)
    return builder.as_markup()


def create_admin_master_keyboard(masters):
    """
    Выбор мастера для редактирования графика.
    callback: sched_<master_id>
    """
    builder = InlineKeyboardBuilder()

    for master in masters:
        builder.button(
            text=master['name'],
            callback_data=f"sched_{master['id']}"
        )

    builder.adjust(1)
    return builder.as_markup()

def create_profile_keyboard():
    """
    Профиль юзера.
    """
    builder = InlineKeyboardBuilder()

    builder.button(text="✏️ Изменить номер", callback_data="change_phone")

    return builder.as_markup()

def create_keyboard_return_master(master_id):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="📅 Записаться к этому мастеру",
        callback_data=f"book_master_{master_id}"
    )
    builder.button(
        text="🔙 Назад",
        callback_data="back_to_masters"
    )

    builder.adjust(1)
    return builder.as_markup()









