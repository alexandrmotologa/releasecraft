"""Unit tests for WebhookDispatcher."""

from unittest.mock import MagicMock, patch

from releasecraft.publisher.webhooks import WebhookDispatcher


@patch("httpx.Client.post")
def test_send_discord_webhook(mock_post: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 204
    mock_post.return_value = mock_resp

    success = WebhookDispatcher.send_discord(
        webhook_url="https://discord.com/api/webhooks/123/abc",
        title="v1.5.0",
        tag_name="v1.5.0",
        release_url="https://github.com/alexandrmotologa/releasecraft/releases/tag/v1.5.0",
        changelog_snippet="Added OAuth2 login support.",
    )
    assert success is True
    assert mock_post.called
    call_kwargs = mock_post.call_args[1]
    assert "embeds" in call_kwargs["json"]


@patch("httpx.Client.post")
def test_send_slack_webhook(mock_post: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    success = WebhookDispatcher.send_slack(
        webhook_url="https://hooks.slack.com/services/123/abc",
        title="v1.5.0",
        tag_name="v1.5.0",
        release_url="https://github.com/alexandrmotologa/releasecraft/releases/tag/v1.5.0",
        changelog_snippet="Added OAuth2 login support.",
    )
    assert success is True
    assert mock_post.called
    call_kwargs = mock_post.call_args[1]
    assert "blocks" in call_kwargs["json"]


@patch("httpx.Client.post")
def test_dispatch_generic_webhook(mock_post: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    success = WebhookDispatcher.dispatch(
        webhook_url="https://example.com/webhook",
        webhook_type="generic",
        title="Release v2.0.0",
        tag_name="v2.0.0",
    )
    assert success is True
    assert mock_post.called
