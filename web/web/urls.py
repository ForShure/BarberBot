from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from shop import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='home'),
    path('get-booked-slots/', views.get_booked_slots, name='get_booked_slots'),
    path('', include('shop.urls')),
]

# Пробиваем стену Докера напрямую:
if settings.DEBUG:
    # Говорим Джанго: "Если кто-то просит /static/, просто иди в папку static и отдавай файл без вопросов!"
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')

    # То же самое для фотографий
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)