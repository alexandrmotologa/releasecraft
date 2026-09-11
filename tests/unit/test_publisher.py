"""Unit tests for GitHubClient and GitPusher."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import git

from releasecraft.publisher.git_pusher import GitPusher
from releasecraft.publisher.github_client import GitHubClient


def test_github_remote_url_extraction() -> None:
    https_url = "https://github.com/alexandrmotologa/releasecraft.git"
    ssh_url = "git@github.com:alexandrmotologa/releasecraft.git"

    assert GitHubClient.extract_repo_from_remote_url(https_url) == "alexandrmotologa/releasecraft"
    assert GitHubClient.extract_repo_from_remote_url(ssh_url) == "alexandrmotologa/releasecraft"


@patch("httpx.Client.post")
def test_github_create_release(mock_post: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "id": 12345,
        "tag_name": "v1.5.0",
        "html_url": "https://github.com/alexandrmotologa/releasecraft/releases/tag/v1.5.0",
    }
    mock_post.return_value = mock_response

    client = GitHubClient(token="mock_token", repo="alexandrmotologa/releasecraft")
    res = client.create_release(
        tag_name="v1.5.0",
        name="v1.5.0",
        body="Release notes",
    )

    assert res["id"] == 12345
    assert "releases/tag/v1.5.0" in res["html_url"]
    assert mock_post.called


def test_git_pusher_dry_run(tmp_path: Path) -> None:
    repo = git.Repo.init(tmp_path)
    # Add dummy remote
    repo.create_remote("origin", "https://github.com/alexandrmotologa/releasecraft.git")

    file1 = tmp_path / "README.md"
    file1.write_text("Hello", encoding="utf-8")
    repo.index.add([str(file1)])
    with repo.config_writer() as cfg:
        cfg.set_value("user", "name", "Test")
        cfg.set_value("user", "email", "test@example.com")
    repo.index.commit("initial")

    pusher = GitPusher(repo, remote_name="origin")
    actions = pusher.push(tag_name="v1.0.0", dry_run=True)

    assert len(actions) == 2
    assert "origin" in actions[0]
    assert "v1.0.0" in actions[1]
