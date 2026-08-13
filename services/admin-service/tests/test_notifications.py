"""Notifications tests (Task 19 §2, §3, §5)."""

from .fixtures import (
    access_token,
    api_client,
    build_app,
    headers,
    scenario,
)

READ_TOKEN = access_token(permissions=("admin:read",))
WRITE_TOKEN = access_token(permissions=("admin:read", "admin:write"))


def test_notification_lifecycle() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        service = app.state.admin_service
        user = await service.create_user(
            subject="recipient",
            email="recipient@example.com",
            display_name="Recipient",
            status="active",
            roles=[],
        )
        async with await api_client(app) as client:
            created = await client.post(
                "/api/v1/admin/notifications",
                headers=headers(token=WRITE_TOKEN),
                json={
                    "recipient_id": user.id,
                    "type": "failure",
                    "title": "Pin publish failed",
                    "body": "pin-9 exceeded retries",
                },
            )
            assert created.status_code == 201
            notification = created.json()
            assert notification["status"] == "unread"

            listed = (
                await client.get("/api/v1/admin/notifications", headers=headers(token=READ_TOKEN))
            ).json()
            # The caller ("tester") is not the recipient -> empty inbox.
            assert listed == []

            own = await service.list_notifications(user.id)
            assert len(own) == 1

            marked = await client.post(
                f"/api/v1/admin/notifications/{notification['id']}/read",
                headers=headers(token=READ_TOKEN),
            )
            # Only the recipient can mark their own notification read.
            assert marked.status_code == 404

    scenario(run)


def test_notification_preferences_roundtrip() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        async with await api_client(app) as client:
            initial = (
                await client.get(
                    "/api/v1/admin/notifications/preferences", headers=headers(token=READ_TOKEN)
                )
            ).json()
            assert initial["channels"] == ["inbox"]

            updated = await client.put(
                "/api/v1/admin/notifications/preferences",
                headers=headers(token=READ_TOKEN),
                json={
                    "channels": ["inbox", "email"],
                    "quiet_hours": {"start": "22:00", "end": "08:00"},
                },
            )
            assert updated.status_code == 200
            body = updated.json()
            assert body["channels"] == ["inbox", "email"]
            assert body["quiet_hours"]["start"] == "22:00"

    scenario(run)
