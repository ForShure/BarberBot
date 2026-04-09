from django.shortcuts import render, redirect
from .models import Master, TelegramUser, DayOff, Appointment, Service
from .forms import AppointmentForm
from django.http import JsonResponse
import os
import json
from .serializers import MasterSerializer, ServiceSerializer, AppointmentSerializer
from rest_framework import generics

ADMIN_ID = os.getenv("ADMIN_ID")

def index(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = AppointmentForm()

    masters = Master.objects.all()

    day_offs_dict = {}
    for do in DayOff.objects.all():
        master_id = do.master.id
        date_str = do.date.strftime('%Y-%m-%d')  # Превращаем дату в строку

        if master_id not in day_offs_dict:
            day_offs_dict[master_id] = []
        day_offs_dict[master_id].append(date_str)

    # Превращаем Python-словарь в JSON-строку
    day_offs_json = json.dumps(day_offs_dict)

    context = {
        'masters_list': masters,
        'form': form,
        'day_offs_json': day_offs_json  # Передаем это на сайт
    }
    return render(request, 'index.html', context)


def get_booked_slots(request):
    # 1. Получаем параметры из запроса (то, что прислал JS)
    master_id = request.GET.get('master_id')
    date_str = request.GET.get('date')


    if not master_id or not date_str:
        return JsonResponse({'error': 'No data'}, status=400)

    day_off = DayOff.objects.filter(master_id=master_id, date=date_str).exists()

    if day_off:
        return JsonResponse({'day_off': True})

    # 2. Ищем занятые слоты в базе
    booked_times = Appointment.objects.filter(
        master_id=master_id,
        date=date_str
    ).values_list('time', flat=True)


    slots_list = [
        t.strftime('%H:%M')
        for t in booked_times
    ]


    # 3. Отдаем JSON
    return JsonResponse({'booked': slots_list, 'day_off': False})

def webapp_page(request):
    return render(request, 'webapp.html')

class MasterListAPIView(generics.ListAPIView):
    queryset = Master.objects.all()
    serializer_class = MasterSerializer

class ServiceListAPIView(generics.ListAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

class AppointmentCreateAPIView(generics.CreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    def perform_create(self, serializer):
        telegram_chat_id = self.request.data.get('telegram_chat_id')
        print("TELEGRAM ID:", telegram_chat_id)
        if telegram_chat_id:
            client_obj, _ = TelegramUser.objects.get_or_create(chat_id=telegram_chat_id)
            serializer.save(user=client_obj)
        else:
            serializer.save()
