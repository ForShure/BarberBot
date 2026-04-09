from aiogram.filters import BaseFilter
from aiogram.types import Message
from asgiref.sync import sync_to_async
from shop.models import Master

# find id
@sync_to_async
def id_finder(telegram_id):
    return Master.objects.filter(telegram_id=telegram_id).first()

class IsMaster(BaseFilter):
    async def __call__(self, message: Message) :
        master = await id_finder(message.from_user.id)
        if master:
            return True
        return False



