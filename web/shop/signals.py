import requests
import os
import logging
import redis
import gspread

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Master
from .tasks import send_remind
from datetime import datetime, timedelta
from django.conf import settings

# Настраиваем логгер, чтобы сообщения точно были видны в терминале
logger = logging.getLogger(__name__)

redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
def send_to_google_from_django(appointment):
    print("⏳ [DJANGO] Пытаюсь записать в Гугл...")
    try:
        gc = gspread.service_account(filename='google_credentials.json')
        sh = gc.open("Вишенка")
        worksheet = sh.sheet1

        # Достаем телефон безопасно (на случай, если юзера нет)
        phone = appointment.phone if appointment.phone else "Не указан"
        client_name = appointment.client_name if appointment.client_name else "Не указано"

        new_row = [
            str(appointment.date),
            str(appointment.time),
            client_name,
            phone,
            appointment.service.name,
            appointment.master.name,
            str(appointment.service.price)
        ]
        worksheet.append_row(new_row)
        print("✅ [DJANGO] СТРОКА В ГУГЛ УСПЕШНО ДОБАВЛЕНА!")
    except Exception as e:
        print(f"❌ [DJANGO ОШИБКА ГУГЛ]: {e}")

@receiver(post_save, sender='shop.Appointment')
def send_telegram_notification(sender, instance, created, **kwargs):
    logger.info(f"👀 СИГНАЛ СРАБОТАЛ! Запись ID: {instance.id}")

    if not created:
        return

    TOKEN = os.getenv("TOKEN")
    ADMIN_ID = os.getenv("ADMIN_ID")

    if not TOKEN or not ADMIN_ID:
        logger.error(f"❌ Нет токена или ADMIN_ID! TOKEN={TOKEN} ADMIN_ID={ADMIN_ID}")
        return

    try:
        ADMIN_ID = int(ADMIN_ID)
    except ValueError:
        logger.error("❌ ADMIN_ID должен быть числом!")
        return

    service_name = instance.service.name if instance.service else "Не указана"
    master_name = instance.master.name if instance.master else "Не указан"

    current_date = instance.date
    current_time = instance.time

    if isinstance(current_date, str):
        current_date = datetime.strptime(current_date.replace('.', '-'), '%Y-%m-%d').date()
    if isinstance(current_time, str):
        current_time = datetime.strptime(current_time[:5], '%H:%M').time()

    appointment_dt = datetime.combine(current_date, current_time)
    reminder_time = appointment_dt - timedelta(hours=2)
    if reminder_time > datetime.now():
        send_remind.apply_async(args=[instance.id], eta=reminder_time)

    send_to_google_from_django(instance)

    message_admin = (
        f"🚀 <b>НОВАЯ ЗАПИСЬ!</b>\n"
        f"👤 {instance.client_name or 'Не указано'}\n"
        f"📞 {instance.phone or 'Не указан'}\n"
        f"✂️ {master_name} | {service_name}\n"
        f"📅 {instance.date} {instance.time}"
    )

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data_admin = {"chat_id": ADMIN_ID, "text": message_admin, "parse_mode": "HTML"}

    try:
        response = requests.post(url, data=data_admin, timeout=5)
        logger.info(f"📨 Ответ Telegram: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Ответ сервера: {response.text}")
    except Exception as e:
        logger.error(f"💀 КРИТИЧЕСКАЯ ОШИБКА: {e}")

    try:
        if instance.user and instance.user.chat_id:
            message = f"{instance.client_name}, вы успешно записаны к мастеру {master_name} на {current_date} в {current_time}!"
            data = {"chat_id": instance.user.chat_id, "text": message, "parse_mode": "HTML"}

            response_client = requests.post(url, data=data, timeout=5)
            logger.info(f"📨 Ответ Telegram (Клиент): {response_client.status_code}")

            if response_client.status_code != 200:
                logger.error(f"Ответ сервера: {response_client.text}")
    except Exception as e:
        logger.error(f"💀 КРИТИЧЕСКАЯ ОШИБКА: {e}")

    if instance.master and instance.master.telegram_id:
        text_for_master = (
            f"🚀 <b>НОВАЯ ЗАПИСЬ!</b>\n"
            f"👤 Клиент: {instance.client_name or 'С сайта'}\n"
            f"📞 Телефон: <code>{instance.phone or 'Не указан'}</code>\n"
            # Используем безопасные current_date и current_time
            f"📅 Дата: {current_date.strftime('%d.%m.%Y')}\n"
            f"⏰ Время: {current_time.strftime('%H:%M')}\n"
            f"💸 Услуга: {service_name}"
        )
        payload_master = {
            "chat_id": instance.master.telegram_id,
            "text": text_for_master,
            "parse_mode": "HTML"
        }

        try:
            response_master = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json=payload_master,
                                            timeout=5)
            logger.info(f"📨 Ответ Telegram (Мастер): {response_master.status_code}")
        except Exception as e:
            logger.error(f"💀 Ошибка отправки мастеру: {e}")


@receiver(post_save, sender=Master)
@receiver(post_delete, sender=Master)
def catch_event(sender, instance, **kwargs):
    redis_client.delete('masters_list')
    print(f"Кэш мастеров")
