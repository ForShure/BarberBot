from django.apps import AppConfig

class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'

    def ready(self):
        # Этот текст должен появиться в консоли ПРИ ЗАПУСКЕ сервера
        print("🔧 ЗАГРУЗКА ShopConfig... ПОДКЛЮЧАЮ SIGNALS.PY...")
        try:
            import shop.signals
            print("✅ SIGNALS.PY УСПЕШНО ИМПОРТИРОВАН")
        except Exception as e:
            print(f"❌ ОШИБКА ИМПОРТА SIGNALS: {e}")
