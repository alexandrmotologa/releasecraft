"""GitHub Releases provider implementation."""

from pathlib import Path
from typing import Any

from releasecraft.publisher.asset_uploader import AssetUploader
from releasecraft.publisher.github_client import GitHubClient
from releasecraft.publisher.providers.base import ReleaseProvider


class GitHubProvider(ReleaseProvider):
    """Releases provider for GitHub."""

    def __init__(self, token: str | None = None, repo: str | None = None) -> None:
        self.client = GitHubClient(token=token, repo=repo)

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
        """Create a release and optionally upload assets."""
        release_data = self.client.create_release(
            tag_name=tag_name,
            name=name,
            body=body,
            target_commitish=target_commitish,
            draft=draft,
            prerelease=prerelease,
        )

        upload_url = release_data.get("upload_url")
        if upload_url and assets and self.client.token:
            for asset_file in assets:
                try:
                    AssetUploader.upload_github_asset(
                        upload_url_template=upload_url,
                        token=self.client.token,
                        asset_path=asset_file,
                    )
                except Exception as ex:
                    import sys

                    print(
                        f"Warning: Failed to upload release asset {asset_file.name}: {ex}",
                        file=sys.stderr,
                    )

        return release_data
