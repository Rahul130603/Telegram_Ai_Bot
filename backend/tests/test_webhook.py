from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.telegram.webhook import create_webhook_router


class Runtime:
    class Config:
        telegram_webhook_path = "/telegram/webhook"
        telegram_webhook_secret = SecretStr("expected")
    settings = Config()
    async def process_update(self, data): pass


def test_webhook_rejects_secret_and_bad_update():
    app = FastAPI()
    app.state.background_updates = set()
    app.include_router(create_webhook_router(Runtime()))
    client = TestClient(app)
    assert client.post("/telegram/webhook", json={"update_id": 1}).status_code == 403
    headers = {"X-Telegram-Bot-Api-Secret-Token": "expected"}
    assert client.post("/telegram/webhook", json={}, headers=headers).status_code == 400
    assert client.post("/telegram/webhook", json={"update_id": 1}, headers=headers).status_code == 204

