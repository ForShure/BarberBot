from django.db import models

# МАСТЕР (Барбер)

class Master(models.Model):
    # Имя мастера (отображается на сайте и в админке)
    name = models.CharField(
        max_length=50,
        verbose_name="Имя мастера"
    )

    # Фото мастера (загружается в папку media/masters/)
    photo = models.ImageField(
        upload_to='masters/',
        null=True,
        blank=True
    )
    telegram_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Telegram ID мастера",
        help_text="ID аккаунта мастера в Телеграм для доступа к кабинету"
    )

    # Краткое описание (опыт, стиль и т.д.)
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Описание"
    )
    color = models.CharField(
        max_length=7,
        default="#76a2b3"
    )
    def __str__(self):
        # Как объект будет отображаться в админке
        return self.name

    class Meta:
        verbose_name = "Мастер"
        verbose_name_plural = "Мастера"


# TELEGRAM ПОЛЬЗОВАТЕЛЬ
# (Храним тех, кто писал боту)

class TelegramUser(models.Model):
    # Telegram chat_id — уникальный
    chat_id = models.BigIntegerField(unique=True)

    # Username из Telegram (может отсутствовать)
    username = models.CharField(max_length=255, null=True, blank=True)

    # Когда пользователь впервые написал боту
    joined_at = models.DateTimeField(auto_now_add=True)

    # Телефон, если пользователь его передал
    phone = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.chat_id} - {self.username}"

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

# УСЛУГА
class Service(models.Model):
    # Название услуги (Стрижка, Борода и т.д.)
    name = models.CharField(max_length=50)

    # Цена в гривнах
    price = models.IntegerField()

    # Описание услуги
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.price}₴)"

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"

# ЗАПИСЬ НА ПРИЁМ
class Appointment(models.Model):
    # Если запись пришла из Telegram — сохраняем пользователя
    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # Если запись с сайта — имя клиента
    client_name = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    # Телефон клиента
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    # Какая услуга выбрана
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # К какому мастеру запись
    master = models.ForeignKey(
        Master,
        on_delete=models.CASCADE
    )

    # Дата записи
    date = models.DateField()

    # Время записи
    time = models.TimeField()

    def __str__(self):
        return f"{self.master} — {self.date} {self.time}"

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"

        # 🔥 ВАЖНО:
        # Это защита на уровне базы данных.
        # Нельзя записать двух клиентов к одному мастеру
        # на одну дату и одно время.
        constraints = [
            models.UniqueConstraint(
                fields=['master', 'date', 'time'],
                name='unique_master_slot'
            )
        ]

# ВЫХОДНОЙ ДЕНЬ МАСТЕРА
class DayOff(models.Model):
    # У какого мастера выходной
    master = models.ForeignKey(
        Master,
        on_delete=models.CASCADE
    )
    # Конкретная дата выходного
    date = models.DateField()

    class Meta:
        verbose_name = "Выходной"
        verbose_name_plural = "Выходные"

        # 🔥 Нельзя добавить два одинаковых выходных
        constraints = [
            models.UniqueConstraint(
                fields=['master', 'date'],
                name='unique_master_dayoff'
            )
        ]

    def __str__(self):
        return f"{self.master} — выходной {self.date}"




