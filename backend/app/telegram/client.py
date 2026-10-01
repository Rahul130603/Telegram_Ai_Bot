from __future__ import annotations

import io

from telegram import Bot, InlineKeyboardMarkup
from telegram.error import BadRequest, NetworkError, RetryAfter, TimedOut

from app.utils.text import chunks


class PTBTelegramClient:
    def __init__(self, bot: Bot, max_length: int = 4000, parse_mode: str = "none") -> None:
        self.bot, self.max_length = bot, max_length
        self.parse_mode = None if parse_mode == "none" else parse_mode.upper()

    async def get_me(self):
        return await self.bot.get_me()

    async def send_message(self, chat_id: int, text: str, reply_markup: InlineKeyboardMarkup | None = None):
        messages = []
        for index, part in enumerate(chunks(text, self.max_length)):
            try:
                message = await self.bot.send_message(chat_id, part, parse_mode=self.parse_mode, reply_markup=reply_markup if index == len(chunks(text, self.max_length)) - 1 else None)
            except RetryAfter as exc:
                await __import__("asyncio").sleep(float(exc.retry_after))
                message = await self.bot.send_message(chat_id, part, parse_mode=self.parse_mode, reply_markup=reply_markup)
            messages.append(message)
        return messages

    async def send_photo(self, chat_id: int, data: bytes, caption: str = "", reply_markup: InlineKeyboardMarkup | None = None):
        for attempt in range(2):
            try:
                return await self.bot.send_photo(
                    chat_id,
                    photo=io.BytesIO(data),
                    caption=caption[:1024],
                    parse_mode=self.parse_mode,
                    reply_markup=reply_markup,
                    connect_timeout=30,
                    read_timeout=120,
                    write_timeout=120,
                    pool_timeout=30,
                )
            except RetryAfter as exc:
                if attempt:
                    raise
                await __import__("asyncio").sleep(float(exc.retry_after))
            except (TimedOut, NetworkError):
                if attempt:
                    raise
                await __import__("asyncio").sleep(1)
        raise TimedOut("Telegram photo upload timed out")

    async def edit_or_send(self, chat_id: int, message_id: int, text: str, reply_markup: InlineKeyboardMarkup | None = None):
        try:
            return await self.bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, parse_mode=self.parse_mode, reply_markup=reply_markup)
        except BadRequest:
            return (await self.send_message(chat_id, text, reply_markup))[-1]

    async def chat_action(self, chat_id: int, action: str):
        return await self.bot.send_chat_action(chat_id, action)

