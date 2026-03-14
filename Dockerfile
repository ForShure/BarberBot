FROM python:3.12-slim

# Отключаем создание лишних файлов .pyc и включаем логгирование сразу в консоль
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Создаем папку внутри контейнера, где будет жить проект
WORKDIR /app

# Сначала копируем только список зависимостей (для кэширования)
COPY requirements.txt .

# Устанавливаем библиотеки
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код проекта внутрь
COPY . .