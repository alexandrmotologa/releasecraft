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


def test_cli_hook_install_uninstall(repo_with_commits: git.Repo, tmp_path: Path) -> None:
    res_install = runner.invoke(app, ["hook", "install", str(tmp_path)])
    assert res_install.exit_code == 0
    assert "Installed commit-msg hook" in res_install.stdout

    hook_file = tmp_path / ".git" / "hooks" / "commit-msg"
    assert hook_file.is_file()

    res_uninstall = runner.invoke(app, ["hook", "uninstall", str(tmp_path)])
    assert res_uninstall.exit_code == 0
    assert "Successfully removed" in res_uninstall.stdout
    assert not hook_file.is_file()


def test_cli_preview_with_highlights(repo_with_commits: git.Repo, tmp_path: Path) -> None:
    res = runner.invoke(app, ["preview", "--highlights", str(tmp_path)])
    assert res.exit_code == 0
    assert "#### 🌟 Highlights" in res.stdout


def test_cli_release_with_manifest_bump(repo_with_commits: git.Repo, tmp_path: Path) -> None:
    # Add a pyproject.toml
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "demo"\nversion = "1.0.0"\n', encoding="utf-8")
    repo_with_commits.index.add([str(pyproject)])
    repo_with_commits.index.commit("chore: add pyproject.toml")

    # Add feature
    app_py = tmp_path / "app.py"
    app_py.write_text("print('version 2')", encoding="utf-8")
    repo_with_commits.index.add([str(app_py)])
    repo_with_commits.index.commit("feat: add cool feature")

    res = runner.invoke(
        app,
        [
            "release",
            "--no-interactive",
            "--no-push",
            "--no-publish",
            "--bump-manifests",
            str(tmp_path),
        ],
    )
    assert res.exit_code == 0

    # Verify pyproject.toml was bumped to 1.1.0 and committed
    content = pyproject.read_text(encoding="utf-8")
    assert 'version = "1.1.0"' in content


def test_cli_init_command(tmp_path: Path) -> None:
    git.Repo.init(tmp_path)
    res = runner.invoke(app, ["init", str(tmp_path)])
    assert res.exit_code == 0
    assert "Created configuration file" in res.stdout

    config_file = tmp_path / ".releasecraft.yaml"
    assert config_file.is_file()
    content = config_file.read_text(encoding="utf-8")
    assert "tag_format:" in content
    assert "sections:" in content


def test_cli_preview_v0(tmp_path: Path) -> None:
    repo = git.Repo.init(tmp_path)
    with repo.config_writer() as cfg:
        cfg.set_value("user", "name", "Test")
        cfg.set_value("user", "email", "test@example.com")

    f = tmp_path / "app.txt"
    f.write_text("v0", encoding="utf-8")
    repo.index.add([str(f)])
    c = repo.index.commit("chore: init")
    repo.create_tag("v0.2.0", ref=c)

    f.write_text("v1", encoding="utf-8")
    repo.index.add([str(f)])
    repo.index.commit("feat!: breaking change in v0")

    # With --v0, breaking in 0.x should bump to 0.3.0 (minor), NOT 1.0.0
    res = runner.invoke(app, ["preview", "--v0", "--json", str(tmp_path)])
    assert res.exit_code == 0
    data = json.loads(res.stdout)
    assert data["next_version"] == "0.3.0"
    assert data["bump_type"] == "minor"
