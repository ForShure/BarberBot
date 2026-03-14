import logging
from datetime import datetime, timedelta

import pytz
from aiogram import Bot
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone

from shop.models import Master, TelegramUser, Appointment, Service

# СОЗДАНИЕ ЗАПИСИ
@sync_to_async
def create_appointment(user_id: int, master_id: int, service_id: int,
                       date_str: str, time_str: str):
    """
    Создаёт запись клиента.
    Валидирует дату и время.
    Защищено от гонки через transaction.atomic().
    """

    # Парсинг строки в объекты даты/времени
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    time_obj = datetime.strptime(time_str, '%H:%M').time()

    # Используем timezone-aware время (важно для продакшена)
    now = timezone.localtime()
    today = now.date()
    current_time = now.time()

    # ВАЛИДАЦИЯ
    if date_obj < today:
        raise ValueError("Нельзя записаться в прошлое")

    if date_obj == today and time_obj <= current_time:
        raise ValueError("Это время уже прошло")

    try:
        user = TelegramUser.objects.get(chat_id=user_id)
        master = Master.objects.get(id=master_id)
        service = Service.objects.get(id=service_id)
    except ObjectDoesNotExist:
        logging.warning("❗ Ошибка создания записи: объект не найден")
        return None

    # ЗАЩИТА ОТ ДВОЙНОЙ ЗАПИСИ
    with transaction.atomic():
        is_taken = Appointment.objects.filter(
            master=master,
            date=date_obj,
            time=time_obj
        ).exists()

        if is_taken:
            return None

        appointment = Appointment.objects.create(
            master=master,
            service=service,
            user=user,
            date=date_obj,
            time=time_obj,
        )

        logging.info(f"✅ Создана запись {appointment.id}")
        return appointment

# ПОЛУЧЕНИЕ ЗАНЯТЫХ СЛОТОВ
@sync_to_async
def get_taken_slots(master_id: int, date):
    """
    Возвращает список занятых времён в формате HH:MM
    """

    slots = Appointment.objects.filter(
        master_id=master_id,
        date=date
    ).values_list('time', flat=True)

    return [slot.strftime('%H:%M') for slot in slots]

# ПОЛУЧЕНИЕ ЗАПИСЕЙ ПОЛЬЗОВАТЕЛЯ
@sync_to_async
def get_user_appointments(user_id: int):
    today = timezone.localdate()

    appointments = (
        Appointment.objects
        .filter(user__chat_id=user_id, date__gte=today)
        .select_related('master', 'service')
        .order_by('date', 'time')
    )

    return list(appointments)

# УДАЛЕНИЕ ЗАПИСИ
@sync_to_async
def delete_appointment(appointment_id: int) -> bool:
    deleted, _ = Appointment.objects.filter(id=appointment_id).delete()
    return deleted > 0

# УСЛУГИ
@sync_to_async
def get_services():
    return list(Service.objects.all())

# ТЕЛЕФОН ПОЛЬЗОВАТЕЛЯ
@sync_to_async
def save_user_phone(user_id: int, phone: str):
    TelegramUser.objects.filter(chat_id=user_id).update(phone=phone)


@sync_to_async
def get_user_by_chat_id(chat_id: int):
    return TelegramUser.objects.filter(chat_id=chat_id).first()

# ЗАПИСИ НА ДЕНЬ
@sync_to_async
def get_appointments_by_date(date):
    return list(
        Appointment.objects
        .filter(date=date)
        .select_related('master', 'service', 'user')
        .order_by('time')
    )

@sync_to_async
def get_appointments_by_id(appointment_id: int):
    return (
        Appointment.objects
        .select_related('user', 'master', 'service')
        .filter(id=appointment_id)
        .first()
    )



from asgiref.sync import sync_to_async
from django.utils import timezone
from datetime import timedelta
from shop.models import Appointment, Service, TelegramUser


# --- СУЩЕСТВУЮЩИЕ ФУНКЦИИ ---
@sync_to_async
def get_services():
    return list(Service.objects.all())

@sync_to_async
def get_appointments_by_id(app_id):
    try:
        return Appointment.objects.select_related('user', 'master', 'service').get(id=app_id)
    except Appointment.DoesNotExist:
        return None

@sync_to_async
def get_user_appointments(user_id):
    return list(
        Appointment.objects
        .filter(user__chat_id=user_id)
        .select_related('master', 'service')
        .order_by('date', 'time')
    )


@sync_to_async
def get_taken_slots(master_id, date_str):
    return list(
        Appointment.objects
        .filter(master_id=master_id, date=date_str)
        .values_list('time', flat=True)
    )


@sync_to_async
def create_appointment(user_id, master_id, service_id, date_str, time_str):
    try:
        user = TelegramUser.objects.get(chat_id=user_id)

        # Получаем объект телефона из профиля (если есть) или пустоту
        phone_number = user.phone if user.phone else ""

        appointment = Appointment.objects.create(
            user=user,
            master_id=master_id,
            service_id=service_id,
            date=date_str,
            time=time_str,
            client_name=user.username or "Telegram Client",  # Дублируем имя
            phone=phone_number  # Дублируем телефон в саму запись
        )
        return appointment
    except Exception as e:
        print(f"Ошибка создания записи: {e}")
        return None

@sync_to_async
def delete_appointment(app_id):
    Appointment.objects.filter(id=app_id).delete()


# --- НОВАЯ ФУНКЦИЯ ДЛЯ НАПОМИНАНИЙ ---
@sync_to_async
def get_appointments_to_remind():
    """Ищет записи, которые начнутся через 2 часа (+- 5 минут погрешность)"""
    from datetime import timedelta  # Локальный импорт, если его нет вверху
    now = timezone.localtime()
    target_time = now + timedelta(hours=2)

    start_range = target_time - timedelta(minutes=5)
    end_range = target_time + timedelta(minutes=5)

    return list(
        Appointment.objects
        .select_related('user', 'master')
        .filter(
            date=now.date(),
            time__gte=start_range.time(),
            time__lte=end_range.time()
        )
    )

# 👇 ЭТУ ФУНКЦИЮ ТОЖЕ НУЖНО ДОБАВИТЬ (для main.py)
async def send_reminders(bot):
    """Эта функция запускается планировщиком"""
    try:
        appointments = await get_appointments_to_remind()

        for app in appointments:
            if app.user and app.user.chat_id:
                try:
                    text = (
                        f"⏰ <b>НАПОМИНАНИЕ!</b>\n\n"
                        f"Через 2 часа у вас стрижка у мастера {app.master.name}.\n"
                        f"Ждем вас! 💈"
                    )
                    await bot.send_message(chat_id=app.user.chat_id, text=text, parse_mode="HTML")
                except Exception:
                    pass
    except Exception as e:
        print(f"Ошибка напоминаний: {e}")

