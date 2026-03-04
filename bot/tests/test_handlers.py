import asyncio
from types import SimpleNamespace

from bot.handlers import cmd_explain


class DummyClient:
    async def register_chat(self, **kwargs):
        return kwargs

    async def action_by_id(self, action_id: int):
        return {
            "id": action_id,
            "action_type": "rebalance",
            "title": "Rebalance BTC",
            "reason": "band",
            "effect": "reduce risk",
            "status": "new",
            "created_at": "2026-01-01T00:00:00Z",
            "calculation": {},
        }


class DummyMessage:
    def __init__(self):
        self.last = None

    async def reply_text(self, text: str):
        self.last = text


def test_cmd_explain_usage() -> None:
    msg = DummyMessage()
    update = SimpleNamespace(effective_chat=SimpleNamespace(id=1), effective_message=msg)
    context = SimpleNamespace(args=[], application=SimpleNamespace(bot_data={"backend_client": DummyClient(), "bot_timezone": "UTC"}))
    asyncio.run(cmd_explain(update, context))
    assert "Usage" in msg.last
