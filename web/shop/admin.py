from django.contrib import admin
from .models import Master, TelegramUser, Service, Appointment, DayOff
from django.urls import path
from django.http import JsonResponse
from django.template.response import TemplateResponse
from datetime import datetime
from django.db.models import Count, Sum
from django.utils.timezone import now

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
    search_fields = ('id', 'user__username', 'user__chat_id')
    date_hierarchy = 'date'

    ordering = ('date', 'time')

    list_display_links = ('id', 'user')

    list_per_page = 50

    def get_urls(self):
        urls = super().get_urls()

        my_urls = [
            path('calendar/events/', self.admin_site.admin_view(self.calendar_events_api),
                 name='appointment-calendar-events'),
            path('calendar/', self.admin_site.admin_view(self.calendar_view), name='appointment-calendar'),
            path('analytics/api/', self.admin_site.admin_view(self.analytics_api), name='analytics-api'),
        ]

        return my_urls + urls

    def calendar_view(self, request):
        context = dict(
            self.admin_site.each_context(request),
            title="Календарь записей",
        )
        return TemplateResponse(request, "admin/calendar.html", context)

    def calendar_events_api(self, request):
        appointments = Appointment.objects.select_related('master', 'user')

        events = []

        for appointment in appointments:
            start = datetime.combine(
                appointment.date,
                appointment.time
            ).isoformat()

            client_name = appointment.user.username or str(appointment.user.chat_id)

            events.append({
                "title": f"{client_name} - {appointment.master.name}",
                "start": start,
                "url": f"/admin/shop/appointment/{appointment.id}/change/",
                "color": appointment.master.color or "#76a2b3",
            })

        return JsonResponse(events, safe=False)

    def analytics_api(self, request):
        current_month = datetime.now().month
        current_year = datetime.now().year

        stats = Appointment.objects.filter(
            date__month=current_month,
            date__year=current_year
        ).values('master__name').annotate(
            total_appointments=Count('id'),
            total_revenue=Sum('service__price')
        ).order_by('-total_appointments')

        labels = []
        revenue_data = []
        appointments_data = []

        labels = []
        revenue_data = []
        appointments_data = []

        for stat in stats:
            labels.append(stat['master__name'])
            revenue_data.append(stat['total_revenue'] or 0)
            appointments_data.append(stat['total_appointments'] or 0)

        data = {
            "labels": labels,
            "revenue_data": revenue_data,
            "appointments_data": appointments_data
        }

        return JsonResponse(data)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'description')
    search_fields = ('name',)

@admin.register(DayOff)
class DayOffAdmin(admin.ModelAdmin):
    list_display = ('master', 'date')
    list_filter = ('master', 'date')
    date_hierarchy = 'date'
