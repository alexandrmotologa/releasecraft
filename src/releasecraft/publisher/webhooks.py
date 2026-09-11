"""Webhook notifications for release announcements."""

from typing import Any

import httpx


class WebhookDispatcher:
    """Dispatches release notifications to Discord, Slack, and generic webhooks."""

    @staticmethod
    def send_discord(
        webhook_url: str,
        title: str,
        tag_name: str,
        release_url: str,
        changelog_snippet: str,
    ) -> bool:
        """Send notification to Discord webhook."""
        # Trim snippet to 1000 characters if too long
        snippet = changelog_snippet[:1000]
        if len(changelog_snippet) > 1000:
            snippet += "..."

        payload = {
            "embeds": [
                {
                    "title": f"🚀 Released: {title}",
                    "url": release_url or None,
                    "color": 3878635,  # Emerald cyan
                    "description": snippet or f"New release {tag_name} is now available.",
                    "fields": [
                        {"name": "Tag", "value": f"`{tag_name}`", "inline": True},
                    ],
                    "footer": {"text": "Published via ReleaseCraft"},
                }
            ]
        }

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(webhook_url, json=payload)
            return resp.status_code in (200, 204)

    @staticmethod
    def send_slack(
        webhook_url: str,
        title: str,
        tag_name: str,
        release_url: str,
        changelog_snippet: str,
    ) -> bool:
        """Send notification to Slack incoming webhook."""
        snippet = changelog_snippet[:800]
        if len(changelog_snippet) > 800:
            snippet += "..."

        blocks: list[dict[str, Any]] = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🚀 New Release: {title}"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Tag:* `{tag_name}`\n\n```{snippet}```"
                    if snippet
                    else f"*Tag:* `{tag_name}`",
                },
            },
        ]

        if release_url:
            blocks.append(
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View Release"},
                            "url": release_url,
                        }
                    ],
                }
            )

        payload = {"text": f"New Release: {title} ({tag_name})", "blocks": blocks}

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(webhook_url, json=payload)
            return resp.status_code == 200

    @classmethod
    def dispatch(
        cls,
        webhook_url: str,
        webhook_type: str,
        title: str,
        tag_name: str,
        release_url: str = "",
        changelog_snippet: str = "",
    ) -> bool:
        """Dispatch notification based on target webhook type."""
        w_type = webhook_type.lower()
        if w_type == "discord":
            return cls.send_discord(webhook_url, title, tag_name, release_url, changelog_snippet)
        elif w_type == "slack":
            return cls.send_slack(webhook_url, title, tag_name, release_url, changelog_snippet)
        else:
            # Generic POST
            payload = {
                "event": "release_published",
                "title": title,
                "tag_name": tag_name,
                "release_url": release_url,
                "changelog": changelog_snippet,
            }
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(webhook_url, json=payload)
                return resp.status_code in (200, 201, 204)
