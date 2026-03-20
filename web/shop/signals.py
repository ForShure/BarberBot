import requests
import os
import logging
import redis

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Master
from .tasks import send_remind
from datetime import datetime, timedelta

# Настраиваем логгер, чтобы сообщения точно были видны в терминале
logger = logging.getLogger(__name__)

redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

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
    appointment_dt = datetime.combine(instance.date, instance.time)
    reminder_time = appointment_dt - timedelta(hours=2)
    if reminder_time > datetime.now():
        send_remind.apply_async(args=[instance.id], eta=reminder_time)

    message = (
        f"🚀 <b>НОВАЯ ЗАПИСЬ!</b>\n"
        f"👤 {instance.client_name or 'Не указано'}\n"
        f"📞 {instance.phone or 'Не указан'}\n"
        f"✂️ {master_name} | {service_name}\n"
        f"📅 {instance.date} {instance.time}"
    )

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": ADMIN_ID, "text": message, "parse_mode": "HTML"}

    try:
        response = requests.post(url, data=data, timeout=5)
        logger.info(f"📨 Ответ Telegram: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Ответ сервера: {response.text}")
    except Exception as e:
        logger.error(f"💀 КРИТИЧЕСКАЯ ОШИБКА: {e}")

@receiver(post_save, sender=Master)
@receiver(post_delete, sender=Master)
def catch_event(sender, instance, **kwargs):
    redis_client.delete('masters_list')
    print(f"Кэш мастеров")
