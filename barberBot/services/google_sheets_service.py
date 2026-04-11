import gspread
from asgiref.sync import sync_to_async

SHEET_NAME = "Вишенка"

@sync_to_async
def save_to_google_sheet(date, time, client_name, phone, service_name, master_name, price):
    print("⏳ [GOOGLE] НАЧИНАЮ ЗАПИСЬ В ТАБЛИЦУ...")
    try:
        gc = gspread.service_account(filename='google_credentials.json')
        sh = gc.open(SHEET_NAME)
        worksheet = sh.sheet1

        new_row = [str(date), str(time), client_name, phone, service_name, master_name, str(price)]
        worksheet.append_row(new_row)
        print("✅ [GOOGLE] СТРОКА УСПЕШНО ДОБАВЛЕНА!")
        return True
    except Exception as e:
        print(f"❌ [GOOGLE ОШИБКА]: {e}")
        return False