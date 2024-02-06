from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from sys import argv

if len(argv) < 3:
    print("Usage: {} telegram_api_id telegram_api_hash".format(argv[0]))
    exit(1)

api_id = argv[1]
api_hash = argv[2]

with TelegramClient(StringSession(), api_id, api_hash) as client:
    session = client.session.save()
    print(session)
