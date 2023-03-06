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


def is_chat_checking(chat_id):
    result = redis_client.get(f'checking:{chat_id}')
    return result is not None


@client.on(events.NewMessage(pattern='!kickall'))
async def kick_all_non_club(event: Message):
    try:
        check = await pre_checks(event)
        if check:
            return await _kick_all_non_club(event)
    except Exception as e:
        logger.exception(e)
        redis_client.delete(f'cleaning:{event.chat_id}')


@client.on(events.NewMessage(pattern='!checkall'))
async def check_all_non_club(event: Message):
    try:
        check = await pre_checks(event)
        if check:
            return await _check_all_non_club(event)
    except Exception as e:
        logger.exception(e)
        redis_client.delete(f'checking:{event.chat_id}')


async def pre_checks(event: Message):
    if not event.is_group:
        return

    if is_chat_cleaning(event.chat_id):
        await event.reply('Процесс уже идет')
        return

    chat = await client.get_entity(event.chat_id)
    admins = await client.get_participants(chat, filter=types.ChannelParticipantsAdmins)
    admin_ids = [admin.id for admin in admins]

    if event.sender_id not in admin_ids:
        await event.reply('Команда доступна только админам')
        return

    chat_permissions = await client.get_permissions(chat, await client.get_me())

    if not chat_permissions.is_admin:
        await event.reply('Сначала сделайте меня админом')
        return

    if not chat_permissions.participant.admin_rights.ban_users:
        await event.reply('Дайте мне права банить пользователей, ну')
        return

    return True


async def _check_all_non_club(event: Message):
    if is_chat_checking(event.chat_id):
        await event.reply('Проверка уже была запущена')
        return

    counter = 0
    redis_client.setex(f'checking:{event.chat_id}', 60*MINUTE, 1)
    assert is_chat_checking(event.chat_id)
    chat = await client.get_entity(event.chat_id)
    await event.reply('Начинаем проверять людей не из клуба...')

    async for member in client.iter_participants(chat):
        if member.is_self:
            continue

        if member.bot:
            continue

        if isinstance(member.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)):
            continue

        club_user = club.user_by_telegram_id(member.id)
        sleep(1)
        if club_user:
            continue

        result = "Этот не из клуба"
        username = "@" + member.username if member.username else ""
        await event.reply(
            f'{result}: {member.first_name or "%без_имени%"}, {member.last_name or "%без_фамилии%"} {username}')
        counter += 1

    await event.reply(f'Готово. Всего не из клуба: {counter}')


async def _kick_all_non_club(event: Message):
    chat = await client.get_entity(event.chat_id)
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

        club_user = club.user_by_telegram_id(member.id)
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

    redis_client.delete(f'cleaning:{event.chat_id}')
    await event.reply(f'Готово. Кикнуто всего: {counter}')
    await client.kick_participant(chat, 'me')


try:
    client.run_until_disconnected()
finally:
    redis_client.close()
    client.disconnect()
