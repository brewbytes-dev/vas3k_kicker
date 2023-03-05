import logging
import sentry_sdk
from asyncio import sleep

from telethon import TelegramClient, events, types
from telethon.sessions import StringSession
from telethon.tl.custom import Message
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator

from app import config, club

if config.SENTRY_DSN:
    sentry_sdk.init(config.SENTRY_DSN, traces_sample_rate=0.5)

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(funcName)s - %(name)s - %(message)s",
)


client = TelegramClient(StringSession(
    config.SESSION_STRING),
    config.API_ID, config.API_HASH).start()


@client.on(events.NewMessage(pattern='!kickall'))
async def kick_all_non_club(event: Message):
    if not event.is_group:
        return

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
    async for member in client.iter_participants(chat):
        if member.is_self:
            continue

        if member.bot:
            continue

        if isinstance(member.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)):
            continue

        club_user = await club.user_by_telegram_id(member.id)
        await sleep(1)
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

    await event.reply(f'Готово. Кикнуто всего: {counter}')
    # await client.kick_participant(chat, 'me')


try:
    client.run_until_disconnected()
finally:
    client.disconnect()
