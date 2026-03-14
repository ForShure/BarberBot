from django.contrib import admin
from .models import Master, TelegramUser, Service, Appointment, DayOff

@admin.register(TelegramUser)
class TelegramUsersAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'username', 'joined_at')
    search_fields = ('username', 'chat_id')

@admin.register(Master)
class MasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name',)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'master', 'service', 'date', 'time')
    list_filter = ("master", "date", "service")
    search_fields = ('id', 'user__username')
    date_hierarchy = 'date'

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'description')
    search_fields = ('name',)

@admin.register(DayOff)
class DayOffAdmin(admin.ModelAdmin):
    list_display = ('master', 'date')
    list_filter = ('master', 'date')
    date_hierarchy = 'date'
