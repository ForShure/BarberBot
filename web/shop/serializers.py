from rest_framework import serializers
from .models import Master, Service, Appointment


class MasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Master
        fields = ['id', 'name', 'photo', 'description', 'color']

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name']

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['client_name', 'phone', 'master', 'service', 'date', 'time',]