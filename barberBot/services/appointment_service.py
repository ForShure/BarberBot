import logging
import pytz

from config import TIMEZONE
from datetime import datetime, timedelta
from aiogram import Bot
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone

from shop.models import Master, TelegramUser, Appointment, Service, Certificate

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

# --- СУЩЕСТВУЮЩИЕ ФУНКЦИИ ---

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
def delete_appointment(app_id):
    Appointment.objects.filter(id=app_id).delete()


@sync_to_async
def get_master_appointments_by_date(target_date, telegram_id):
    appointments = Appointment.objects.filter(
        date=target_date,
        master__telegram_id=telegram_id
    ).select_related('service', 'user', 'master').order_by('time')

    return list(appointments)

@sync_to_async
def save_certificate(telegram_id, promo, amount):
    certificate, created = Certificate.objects.get_or_create(
        promo=promo,
        defaults={'telegram_id': telegram_id, 'amount': amount}
    )
    return certificate, created

@sync_to_async
def get_user_certificates(telegram_id):
    return list(
        Certificate.objects
        .filter(telegram_id=telegram_id, status=False)
    )

