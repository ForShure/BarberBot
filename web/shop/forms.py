from django import forms
from .models import Appointment, DayOff
from django.utils import timezone

TIME_CHOICES = [
    ('10:00', '10:00'),
    ('11:00', '11:00'),
    ('12:00', '12:00'),
    ('13:00', '13:00'),
    ('14:00', '14:00'),
    ('15:00', '15:00'),
    ('16:00', '16:00'),
    ('17:00', '17:00'),
    ('18:00', '18:00'),
    ('19:00', '19:00'),
    ('20:00', '20:00'),
    ('21:00', '21:00'),
    ('22:00', '22:00'),
]

class AppointmentForm(forms.ModelForm):
    time = forms.ChoiceField(choices=TIME_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Appointment
        fields = ['master', 'service', 'date', 'time', 'client_name', 'phone']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'master': forms.Select(attrs={'class': 'form-select'}),
            'service': forms.Select(attrs={'class': 'form-select'}),
            'client_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_date(self):
        date = self.cleaned_data['date']
        if date < timezone.now().date():
            raise forms.ValidationError("Нельзя записаться на прошедшую дату!")
        return date

    def clean(self):
        cleaned_data = super().clean()
        master = cleaned_data.get('master')
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')

        # ПРОВЕРКА НА ЗАНЯТОЕ ВРЕМЯ (Дубль)
        if master and date and time:
            if Appointment.objects.filter(master=master, date=date, time=time).exists():
                # Вешаем ошибку прямо на поле 'time'.
                self.add_error('time', "Это время уже занято! Кто-то успел быстрее ⚡")

        # ПРОВЕРКА НА ВЫХОДНОЙ
        if master and date:
            if DayOff.objects.filter(master=master, date=date).exists():
                raise forms.ValidationError(f"В этот день у мастера {master.name} выходной! 🏖️")

        return cleaned_data

