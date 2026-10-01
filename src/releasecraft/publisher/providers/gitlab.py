"""GitLab Releases API provider."""

import os
import urllib.parse
from pathlib import Path
from typing import Any

import httpx

from releasecraft.publisher.providers.base import ReleaseProvider


class GitLabProvider(ReleaseProvider):
    """Releases provider for GitLab instances."""

    def __init__(
        self,
        token: str | None = None,
        project_id: str = "",
        base_url: str = "https://gitlab.com",
    ) -> None:
        self.token = token or os.getenv("GITLAB_TOKEN") or os.getenv("GL_TOKEN") or ""
        self.project_id = urllib.parse.quote(project_id, safe="")
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
        """Create a release via GitLab API."""
        url = f"{self.base_url}/api/v4/projects/{self.project_id}/releases"
        headers = {
            "PRIVATE-TOKEN": self.token,
            "Content-Type": "application/json",
            "User-Agent": "ReleaseCraft",
        }
        payload = {
            "name": name,
            "tag_name": tag_name,
            "description": body,
            "ref": target_commitish,
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code in (200, 201):
                return resp.json()
            raise RuntimeError(f"GitLab release creation failed ({resp.status_code}): {resp.text}")
