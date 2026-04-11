import gspread
from asgiref.sync import sync_to_async
import logging

SHEET_NAME = "Вишенка"

@sync_to_async
def save_to_google_sheet(date, time, client_name, phone, service_name, master_name, price):
    try:
        # Авторизуемся через наш секретный файл
        gc = gspread.service_account(filename='google_credentials.json')
        # Находим таблицу по имени и открываем первый лист
        sh = gc.open(SHEET_NAME)
        worksheet = sh.sheet1

        # Формируем строку (список) с данными
        new_row = [str(date), str(time), client_name, phone, service_name, master_name, str(price)]
        worksheet.append_row(new_row)
        return True
    except Exception as e:
        logging.error(f"Ошибка записи в Гугл Таблицу: {e}")
        return False
