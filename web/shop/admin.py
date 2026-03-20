from django.contrib import admin
from .models import Master, TelegramUser, Service, Appointment, DayOff
from django.urls import path
from django.http import JsonResponse
from django.template.response import TemplateResponse
from datetime import datetime
from django.utils import timezone
from django.db.models import Count, Sum

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

        custom_urls = [
            path(
                "calendar/",
                self.admin_site.admin_view(self.calendar_view),
                name="appointment-calendar",
            ),
            path(
                "calendar/events/",
                self.admin_site.admin_view(self.calendar_events_api),
                name="appointment-calendar-events",
            ),
            path(
                "analytics/api/",
                self.admin_site.admin_view(self.analytics_api),
                name="analytics-api",
            ),
        ]

        return custom_urls + urls

    def calendar_view(self, request):
        context = {
            **self.admin_site.each_context(request),
            "title": "Календарь записей",
        }

        return TemplateResponse(request, "admin/calendar.html", context)

    def calendar_events_api(self, request):
        start = request.GET.get("start")
        end = request.GET.get("end")

        appointments = Appointment.objects.select_related("master", "user", "service")

        if start and end:
            appointments = appointments.filter(
                date__gte=start,
                date__lte=end
            )

        events = [
            {
                "title": f"{a.user.username or a.user.chat_id} - {a.master.name}",
                "start": datetime.combine(a.date, a.time).isoformat(),
                "url": f"/admin/shop/appointment/{a.id}/change/",
                "color": a.master.color or "#76a2b3",
            }
            for a in appointments
        ]

        return JsonResponse(events, safe=False)

    def analytics_api(self, request):
        now_time = timezone.now()

        stats = (
            Appointment.objects.filter(date__year=now_time.year, date__month=now_time.month)
            .values("master__name")
            .annotate(
                total_appointments=Count("id"),
                total_revenue=Sum("service__price"),
            )
            .order_by("-total_appointments")
        )

        labels = [s["master__name"] for s in stats]
        revenue_data = [s["total_revenue"] or 0 for s in stats]
        appointments_data = [s["total_appointments"] for s in stats]

        data = {
            "labels": labels,
            "revenue_data": revenue_data,
            "appointments_data": appointments_data,
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
