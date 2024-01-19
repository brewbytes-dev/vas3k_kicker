from telethon.sync import TelegramClient
from telethon.sessions import StringSession

from app.config import API_HASH, API_ID

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    session = client.session.save()
    print(session)
