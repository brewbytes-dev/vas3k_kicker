import asyncio
import logging
from time import sleep

import sentry_sdk
from redis.client import Redis

from telethon import TelegramClient, events, types
from telethon.sessions import StringSession
from telethon.tl.custom import Message
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator
from app import config, club

if config.SENTRY_DSN:
    sentry_sdk.init(config.SENTRY_DSN, traces_sample_rate=0.5)

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(funcName)s - %(name)s - %(message)s",
)

client = TelegramClient(StringSession(
    config.SESSION_STRING),
    config.API_ID, config.API_HASH).start()

redis_client = Redis.from_url(config.REDIS_URL)
redis_client.flushall()

SECOND, MINUTE = 1, 60


def is_chat_cleaning(chat_id):
    result = redis_client.get(f'cleaning:{chat_id}')
    return result is not None


@client.on(events.NewMessage(pattern='!kickall'))
async def kick_all_non_club(event: Message):
    try:
        return await _kick_all_non_club(event)
    except Exception as e:
        logger.exception(e)
        redis_client.delete(f'cleaning:{event.chat_id}')


async def _kick_all_non_club(event: Message):
    if not event.is_group:
        return

    if is_chat_cleaning(event.chat_id):
        return await event.reply('Процесс уже идет')

    chat = await client.get_entity(event.chat_id)
    admins = await client.get_participants(chat, filter=types.ChannelParticipantsAdmins)
    admin_ids = [admin.id for admin in admins]

    if event.sender_id not in admin_ids:
        return await event.reply('Команда доступна только админам')

    chat_permissions = await client.get_permissions(chat, await client.get_me())

    if not chat_permissions.is_admin:
        return await event.reply('Сначала сделайте меня админом')

    if not chat_permissions.participant.admin_rights.ban_users:
        return await event.reply('Дайте мне права банить пользователей, ну')

    counter = 0
    redis_client.setex(f'cleaning:{event.chat_id}', 60*MINUTE, 1)
    assert is_chat_cleaning(event.chat_id)
    await event.reply('Начинаем вышибать людей не из клуба...')
    async for member in client.iter_participants(chat):
        if member.is_self:
            continue

        if member.bot:
            continue

        if isinstance(member.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)):
            continue

        club_user = await club.sync_get_member_by_telegram_id(member.id)
        sleep(1)
        if club_user:
            continue

        permissions = await client.get_permissions(chat, member)
        if permissions.is_banned:
            result = "Кикнут и забанен"
            await client.edit_permissions(chat, member, view_messages=False)
        else:
            try:
                result = "Кикнут"
                await client.kick_participant(chat, member.id)
            except:
                continue

        username = "@" + member.username if member.username else ""
        await event.reply(
            f'{result}: {member.first_name or "%без_имени%"}, {member.last_name or "%без_фамилии%"} {username}')
        counter += 1

    await asyncio.sleep(60)
    redis_client.delete(f'cleaning:{event.chat_id}')
    await event.reply(f'Готово. Кикнуто всего: {counter}')
    await client.kick_participant(chat, 'me')


try:
    client.run_until_disconnected()
finally:
    redis_client.close()
    client.disconnect()
