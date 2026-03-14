from shop.models import TelegramUser
async def register_user(chat_id: int, username: str):
    user = await TelegramUser.objects.aget_or_create(
            chat_id=chat_id,
            defaults={"username": username})
    return user

