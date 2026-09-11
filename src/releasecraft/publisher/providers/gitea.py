"""Gitea and Forgejo Releases API provider."""

from pathlib import Path
from typing import Any

import httpx

from releasecraft.publisher.providers.base import ReleaseProvider


class GiteaProvider(ReleaseProvider):
    """Releases provider for Gitea / Forgejo instances."""

    def __init__(
        self,
        token: str,
        repo: str,
        base_url: str = "https://gitea.com",
    ) -> None:
        self.token = token
        self.repo = repo.strip("/")
        self.base_url = base_url.rstrip("/")

    def create_release(
        self,
        tag_name: str,
        name: str,
        body: str,
        target_commitish: str = "main",
        draft: bool = False,
        prerelease: bool = False,
        assets: list[Path] | None = None,
    ) -> dict[str, Any]:
        """Create a release via Gitea API."""
        url = f"{self.base_url}/api/v1/repos/{self.repo}/releases"
        headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "ReleaseCraft",
        }
        payload = {
            "tag_name": tag_name,
            "title": name,
            "body": body,
            "target_commitish": target_commitish,
            "draft": draft,
            "prerelease": prerelease,
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code in (200, 201):
                return resp.json()
            raise RuntimeError(f"Gitea release creation failed ({resp.status_code}): {resp.text}")
