def test_register_patch_list_telegram_chats(client) -> None:
    reg = client.post(
        "/v1/telegram/chats/register",
        json={
            "chat_id": 123456,
            "timezone": "Europe/Riga",
            "daily_enabled": True,
            "weekly_enabled": True,
        },
    )
    assert reg.status_code == 200
    assert reg.json()["chat_id"] == 123456

    patch = client.patch(
        "/v1/telegram/chats/123456",
        json={"weekly_enabled": False},
    )
    assert patch.status_code == 200
    assert patch.json()["weekly_enabled"] is False

    listed = client.get("/v1/telegram/chats")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
