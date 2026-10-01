import pytest

from app.telegram.client import PTBTelegramClient


class Bot:
    def __init__(self):
        self.messages = []

    async def send_message(self, chat_id, text, **kwargs):
        self.messages.append((chat_id, text, kwargs))
        return text

    async def send_photo(self, chat_id, **kwargs):
        return kwargs


@pytest.mark.asyncio
async def test_chunking_and_parse_mode_safety(png_bytes):
    bot = Bot()
    client = PTBTelegramClient(bot, max_length=5, parse_mode="none")
    await client.send_message(1, "hello world")
    assert [item[1] for item in bot.messages] == ["hello", "world"]
    assert all(item[2]["parse_mode"] is None for item in bot.messages)
    sent = await client.send_photo(1, png_bytes, "caption")
    assert sent["caption"] == "caption"
    assert sent["write_timeout"] == 120
    assert sent["read_timeout"] == 120

