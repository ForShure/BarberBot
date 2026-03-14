import os
import sys
import django
from dotenv import load_dotenv


def setup():
    # 1. Получаем путь к папке бота (/app/barberBot)
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

    # 2. Получаем корень проекта (/app)
    BASE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

    # 3. Путь к папке с Django (/app/web)
    # Добавляем его в sys.path, чтобы Python видел модуль 'web' внутри
    WEB_ROOT = os.path.join(BASE_DIR, "web")

    if WEB_ROOT not in sys.path:
        sys.path.insert(0, WEB_ROOT)

    # 4. Загружаем переменные окружения
    load_dotenv(os.path.join(WEB_ROOT, ".env"))

    # 5. Стартуем Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings")
    django.setup()


# 🔥 ВАЖНО: Запускаем настройку СРАЗУ (без всяких if)
setup()