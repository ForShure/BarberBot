import json
import redis.asyncio as redis

from asgiref.sync import sync_to_async
from shop.models import Master, DayOff, Service
from datetime import datetime, timedelta


redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

@sync_to_async
def _get_masters_from_db():
    return list(Master.objects.values('id', 'name'))

async def get_all_masters():
    cached_masters = await redis_client.get('masters_list')
    if cached_masters:
        return json.loads(cached_masters)
    else:
        masters_list = await _get_masters_from_db()
        await redis_client.setex('masters_list', 3600, json.dumps(masters_list))
        return masters_list

@sync_to_async
def toggle_day_off(master_id, date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    day_off_record = DayOff.objects.filter(master_id=master_id, date=date_obj).first()

    if day_off_record:
        day_off_record.delete()
        return False

    else:
        DayOff.objects.create(master_id=master_id, date=date_obj)
        return True

@sync_to_async
def get_weekends_days(master_id):
    days = DayOff.objects.filter(master_id=master_id)
    return [str(day.date) for day in days]

@sync_to_async
def get_master_by_id(master_id):
    return Master.objects.filter(id=master_id).first()

@sync_to_async
def get_service_by_id(service):
    return Service.objects.filter(id=service).first()