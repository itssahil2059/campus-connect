"""WebSocket tests: run the real ASGI app (origin check + token login +
routing + consumer) in memory with Channels' WebsocketCommunicator.

transaction=True because the consumer reads the database from another
thread, which can't see data inside the normal per-test transaction.
"""
from contextlib import asynccontextmanager

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from rest_framework.authtoken.models import Token

from chat import consumers
from chat.models import Message
from chat.services import send_message
from connections.models import Connection
from core.asgi import application

pytestmark = [pytest.mark.asyncio, pytest.mark.django_db(transaction=True)]

ORIGIN = (b"origin", b"http://localhost")


def token_for(user):
    return Token.objects.get_or_create(user=user)[0].key


@pytest.fixture
def tokens(alice, bob, carol):
    return {u.username: token_for(u) for u in (alice, bob, carol)}


@asynccontextmanager
async def socket(conversation_id, token=None, headers=(ORIGIN,)):
    path = f"/ws/chat/{conversation_id}/"
    if token:
        path += f"?token={token}"
    communicator = WebsocketCommunicator(application, path, headers=list(headers))
    try:
        yield communicator
    finally:
        await communicator.disconnect()


async def assert_closed_with(communicator, code):
    connected, _ = await communicator.connect()
    assert connected  # accepted first, so the browser sees our close code
    assert await communicator.receive_output() == {"type": "websocket.close", "code": code}


class TestConnect:
    async def test_no_token_closes_4401(self, chat_ab):
        async with socket(chat_ab.id) as ws:
            await assert_closed_with(ws, consumers.CLOSE_NOT_LOGGED_IN)

    async def test_bad_token_closes_4401(self, chat_ab):
        async with socket(chat_ab.id, token="not-a-real-token") as ws:
            await assert_closed_with(ws, consumers.CLOSE_NOT_LOGGED_IN)

    async def test_outsider_closes_4403(self, chat_ab, tokens):
        async with socket(chat_ab.id, tokens["carol"]) as ws:
            await assert_closed_with(ws, consumers.CLOSE_NOT_IN_CHAT)

    async def test_missing_conversation_closes_4403(self, chat_ab, tokens):
        async with socket(999999, tokens["alice"]) as ws:
            await assert_closed_with(ws, consumers.CLOSE_NOT_IN_CHAT)

    async def test_other_site_origin_rejected(self, chat_ab, tokens):
        async with socket(chat_ab.id, tokens["alice"], headers=[(b"origin", b"http://evil.example")]) as ws:
            connected, _ = await ws.connect()
            assert not connected

    async def test_participant_connects(self, chat_ab, tokens):
        async with socket(chat_ab.id, tokens["alice"]) as ws:
            connected, _ = await ws.connect()
            assert connected


class TestMessages:
    async def test_message_reaches_both_sides_and_is_saved(self, chat_ab, alice, tokens):
        async with socket(chat_ab.id, tokens["alice"]) as a, socket(chat_ab.id, tokens["bob"]) as b:
            await a.connect()
            await b.connect()

            await a.send_json_to({"type": "message", "body": "  hi bob  "})

            to_bob = await b.receive_json_from()
            to_alice = await a.receive_json_from()  # sender gets the saved copy (with id)

        assert to_bob == to_alice
        assert to_bob["type"] == "message"
        message = to_bob["message"]
        assert message["body"] == "hi bob"
        assert message["sender_id"] == alice.id
        assert message["conversation_id"] == chat_ab.id
        saved = await database_sync_to_async(Message.objects.get)()
        assert saved.id == message["id"]

    async def test_rest_send_is_pushed_live(self, chat_ab, alice, tokens):
        async with socket(chat_ab.id, tokens["bob"]) as b:
            await b.connect()

            await database_sync_to_async(send_message)(chat_ab, alice, "sent over REST")

            event = await b.receive_json_from()
        assert event["message"]["body"] == "sent over REST"

    async def test_invalid_messages_get_errors(self, chat_ab, tokens):
        async with socket(chat_ab.id, tokens["alice"]) as a:
            await a.connect()

            await a.send_json_to({"type": "message", "body": "   "})
            blank = await a.receive_json_from()
            await a.send_json_to({"type": "message", "body": "x" * 2001})
            too_long = await a.receive_json_from()
            await a.send_json_to({"type": "dance"})
            unknown = await a.receive_json_from()

        assert [blank["type"], too_long["type"], unknown["type"]] == ["error"] * 3
        assert unknown["detail"] == "Unknown message type."
        assert await database_sync_to_async(Message.objects.count)() == 0

    async def test_cannot_send_after_disconnect(self, chat_ab, tokens):
        async with socket(chat_ab.id, tokens["alice"]) as a:
            await a.connect()
            await database_sync_to_async(Connection.objects.all().delete)()

            await a.send_json_to({"type": "message", "body": "hi"})
            reply = await a.receive_json_from()

        assert reply == {"type": "error", "detail": "You can only message your connections."}

    async def test_read_receipt(self, chat_ab, alice, bob, tokens):
        await database_sync_to_async(send_message)(chat_ab, bob, "hi alice")
        async with socket(chat_ab.id, tokens["alice"]) as a, socket(chat_ab.id, tokens["bob"]) as b:
            await a.connect()
            await b.connect()

            await a.send_json_to({"type": "read"})
            event = await b.receive_json_from()

        assert event["type"] == "read"
        assert event["reader_id"] == alice.id
        assert event["read_at"]

    async def test_rate_limit(self, chat_ab, tokens, monkeypatch):
        monkeypatch.setattr(consumers, "RATE_LIMIT", 2)
        async with socket(chat_ab.id, tokens["alice"]) as a:
            await a.connect()
            replies = []
            for _ in range(3):
                await a.send_json_to({"type": "message", "body": "hi"})
                replies.append((await a.receive_json_from())["type"])

        assert replies == ["message", "message", "error"]
