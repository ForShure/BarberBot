from django.urls import path
from .views import MasterListAPIView, ServiceListAPIView, get_booked_slots, webapp_page  # Проверь импорты!

urlpatterns = [
    # ... тут админка и главная страница ...

    # ВОТ ЭТА СТРОЧКА ПРОПАЛА, ВЕРНИ ЕЁ:
    path('webapp/', webapp_page, name='webapp'),

    # Твои API и слоты:
    path('get-booked-slots/', get_booked_slots, name='get_booked_slots'),
    path('api/masters/', MasterListAPIView.as_view(), name='api-masters'),
    path('api/services/', ServiceListAPIView.as_view(), name='api-services'),
]