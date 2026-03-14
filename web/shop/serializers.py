from rest_framework import serializers
from .models import Master, Service

class MasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Master
        fields = ['id', 'name']

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        # Проверь, чтобы в модели было поле name (или замени на title/название)
        fields = ['id', 'name']