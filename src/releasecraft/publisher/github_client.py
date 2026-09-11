"""GitHub REST API client for publishing releases."""

import os
import re
import subprocess
from typing import Any

import httpx

GITHUB_API_BASE = "https://api.github.com"
GITHUB_REMOTE_REGEX = re.compile(
    r"(?:git@github\.com:|https://github\.com/)(?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?"
)


class GitHubClient:
    """Publishes release notes and tags to GitHub Releases."""

    def __init__(
        self,
        token: str | None = None,
        repo: str | None = None,
    ) -> None:
        self.token = token or self.discover_token()
        self.repo = repo

    @staticmethod
    def discover_token() -> str | None:
        """Find token from environment variables or local gh CLI."""
        env_token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        if env_token:
            return env_token.strip()

        # Fallback to local gh auth token
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass

        return None

    @staticmethod
    def extract_repo_from_remote_url(remote_url: str) -> str | None:
        """Extract 'owner/repo' from GitHub remote URL."""
        match = GITHUB_REMOTE_REGEX.search(remote_url)
        if match:
            return f"{match.group('owner')}/{match.group('repo')}"
        return None

    def create_release(
        self,
        tag_name: str,
        name: str,
        body: str,
        repo: str | None = None,
        target_commitish: str = "main",
        draft: bool = False,
        prerelease: bool = False,
    ) -> dict[str, Any]:
        """Publish a release to GitHub via REST API.

        Args:
            tag_name: Git tag name (e.g. v1.2.0).
            name: Title of the release.
            body: Release notes markdown body.
            repo: 'owner/repo' format (defaults to self.repo).
            target_commitish: Target branch or commit SHA.
            draft: Whether to save as an unpublished draft.
            prerelease: Whether this release is a pre-release.

        Returns:
            JSON response dictionary from GitHub API.
        """
        target_repo = repo or self.repo
        if not target_repo:
            raise ValueError("GitHub repository ('owner/repo') is required to publish a release.")

        if not self.token:
            raise ValueError("GITHUB_TOKEN or GitHub CLI authentication is required.")

        url = f"{GITHUB_API_BASE}/repos/{target_repo}/releases"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ReleaseCraft",
        }
        payload = {
            "tag_name": tag_name,
            "target_commitish": target_commitish,
            "name": name,
            "body": body,
            "draft": draft,
            "prerelease": prerelease,
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=payload)
            if response.status_code == 201:
                return response.json()

            # Handle errors
            error_detail = response.text
            try:
                data = response.json()
                error_detail = data.get("message", error_detail)
            except Exception:
                pass

            raise RuntimeError(
                f"GitHub release creation failed (HTTP {response.status_code}): {error_detail}"
            )
