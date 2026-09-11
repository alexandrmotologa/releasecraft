"""Unit tests for multi-forge release providers."""

from unittest.mock import MagicMock, patch

from releasecraft.publisher.providers.gitea import GiteaProvider
from releasecraft.publisher.providers.github import GitHubProvider
from releasecraft.publisher.providers.gitlab import GitLabProvider


@patch("httpx.Client.post")
def test_github_provider(mock_post: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"id": 1, "html_url": "https://github.com/..."}
    mock_post.return_value = mock_resp

    provider = GitHubProvider(token="mock_token", repo="owner/repo")
    res = provider.create_release("v1.0.0", "v1.0.0", "Notes")
    assert res["id"] == 1


@patch("httpx.Client.post")
def test_gitlab_provider(mock_post: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"tag_name": "v1.0.0", "name": "v1.0.0"}
    mock_post.return_value = mock_resp

    provider = GitLabProvider(token="mock_token", project_id="12345")
    res = provider.create_release("v1.0.0", "v1.0.0", "Notes")
    assert res["tag_name"] == "v1.0.0"


@patch("httpx.Client.post")
def test_gitea_provider(mock_post: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"id": 99, "tag_name": "v1.0.0"}
    mock_post.return_value = mock_resp

    provider = GiteaProvider(token="mock_token", repo="owner/repo")
    res = provider.create_release("v1.0.0", "v1.0.0", "Notes")
    assert res["id"] == 99
