"""Integration tests for ReleaseCraft CLI commands on synthetic git repositories."""

import json
from pathlib import Path

import git
import pytest
from typer.testing import CliRunner

from releasecraft.cli import app

runner = CliRunner()


@pytest.fixture
def repo_with_commits(tmp_path: Path) -> git.Repo:
    """Fixture providing a synthetic git repository with conventional commits."""
    repo = git.Repo.init(tmp_path)
    with repo.config_writer() as cfg:
        cfg.set_value("user", "name", "ReleaseBot")
        cfg.set_value("user", "email", "bot@example.com")

    # Initial commit with tag v1.0.0
    file1 = tmp_path / "app.py"
    file1.write_text("print('hello')", encoding="utf-8")
    repo.index.add([str(file1)])
    c1 = repo.index.commit("chore: initial commit")
    repo.create_tag("v1.0.0", ref=c1, message="Release v1.0.0")

    # Unreleased commits
    file1.write_text("print('hello world')", encoding="utf-8")
    repo.index.add([str(file1)])
    repo.index.commit("feat(ui): add modern responsive layout (#10)")

    file2 = tmp_path / "fix.py"
    file2.write_text("# fix", encoding="utf-8")
    repo.index.add([str(file2)])
    repo.index.commit("fix(db): handle disconnect exception (#12)")

    return repo


def test_cli_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "ReleaseCraft" in result.stdout


def test_cli_check(repo_with_commits: git.Repo, tmp_path: Path) -> None:
    result = runner.invoke(app, ["check", str(tmp_path)])
    assert result.exit_code == 0
    assert "feat" in result.stdout
    assert "fix" in result.stdout
    assert "ui" in result.stdout


def test_cli_preview_json(repo_with_commits: git.Repo, tmp_path: Path) -> None:
    result = runner.invoke(app, ["preview", "--json", str(tmp_path)])
    assert result.exit_code == 0

    data = json.loads(result.stdout)
    assert data["current_version"] == "1.0.0"
    assert data["next_version"] == "1.1.0"
    assert data["bump_type"] == "minor"
    assert data["commit_count"] == 2
    assert "### 🚀 Features" in data["changelog"]
    assert "### 🐛 Bug Fixes" in data["changelog"]


def test_cli_changelog_command(repo_with_commits: git.Repo, tmp_path: Path) -> None:
    result = runner.invoke(app, ["changelog", str(tmp_path)])
    assert result.exit_code == 0

    changelog_path = tmp_path / "CHANGELOG.md"
    assert changelog_path.is_file()
    content = changelog_path.read_text(encoding="utf-8")
    assert "## [1.1.0]" in content
    assert "add modern responsive layout" in content


def test_cli_release_dry_run(repo_with_commits: git.Repo, tmp_path: Path) -> None:
    tags_before = [t.name for t in repo_with_commits.tags]
    result = runner.invoke(app, ["release", "--dry-run", str(tmp_path)])
    assert result.exit_code == 0
    assert "[DRY RUN MODE]" in result.stdout

    # Verify no new tags were created
    tags_after = [t.name for t in repo_with_commits.tags]
    assert tags_before == tags_after


def test_cli_full_release_execution(repo_with_commits: git.Repo, tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "release",
            "--no-interactive",
            "--no-push",
            "--no-publish",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    assert "Release v1.1.0 completed successfully!" in result.stdout

    # Verify git tag was created
    tag_names = [t.name for t in repo_with_commits.tags]
    assert "v1.1.0" in tag_names

    # Verify CHANGELOG.md exists and is committed
    changelog_path = tmp_path / "CHANGELOG.md"
    assert changelog_path.is_file()
    assert "## [1.1.0]" in changelog_path.read_text(encoding="utf-8")

    # Verify HEAD commit is the release chore
    head_msg = repo_with_commits.head.commit.message
    assert head_msg.strip() == "chore(release): v1.1.0"
