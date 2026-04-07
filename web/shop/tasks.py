import requests

from celery import shared_task
from .models import Appointment
from django.conf import settings

@shared_task
def send_remind(appointment_id):
    appointment = Appointment.objects.filter(id=appointment_id).first()
    token = settings.TOKEN
    if appointment:
        if appointment.user:
            text_for_user = f"Запись к мастеру {appointment.master} будет в {appointment.time}, не опаздывайте"
            urls = f"https://api.telegram.org/bot{token}/sendMessage"
            payload= {
                "chat_id": appointment.user.chat_id,
                "text": text_for_user,
            }
            requests.post(urls, json=payload)

