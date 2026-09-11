"""Unit tests for ChangelogBuilder and ChangelogUpdater."""

from datetime import UTC, datetime
from pathlib import Path

from releasecraft.changelog.builder import ChangelogBuilder
from releasecraft.changelog.updater import ChangelogUpdater
from releasecraft.models import RawCommit, SemVerInfo
from releasecraft.parser.commit_parser import CommitParser


def make_commit(message: str) -> CommitParser:
    raw = RawCommit(
        hash="abcdef1234567890abcdef1234567890abcdef12",
        short_hash="abcdef1",
        author_name="Dev",
        author_email="dev@example.com",
        timestamp=datetime.now(UTC),
        message=message,
    )
    return CommitParser.parse(raw)


def test_changelog_builder_grouping() -> None:
    commits = [
        make_commit("feat(auth): support oauth2 logins"),
        make_commit("fix(db): fix connection leak on error"),
        make_commit("perf(cache): speed up lookups"),
        make_commit("chore(deps): bump httpx"),
    ]
    version = SemVerInfo(major=1, minor=1, patch=0)
    builder = ChangelogBuilder()

    md, sections = builder.build_markdown(
        version=version,
        commits=commits,
        date_str="2026-09-11",
    )

    assert "## [1.1.0] - 2026-09-11" in md
    assert "### 🚀 Features" in md
    assert "- **auth**: support oauth2 logins" in md
    assert "### 🐛 Bug Fixes" in md
    assert "- **db**: fix connection leak on error" in md
    assert "### ⚡ Performance Improvements" in md
    assert "- **cache**: speed up lookups" in md
    # chore is hidden by default
    assert "### 🔧 Maintenance" not in md


def test_changelog_builder_breaking_changes() -> None:
    commits = [
        make_commit("feat!: remove deprecated v1 api endpoints"),
        make_commit("fix: resolve crash on null input"),
    ]
    version = SemVerInfo(major=2, minor=0, patch=0)
    builder = ChangelogBuilder()

    md, _ = builder.build_markdown(version=version, commits=commits, date_str="2026-09-11")

    assert "### ⚠️ Breaking Changes" in md
    assert "remove deprecated v1 api endpoints" in md


def test_changelog_updater_new_file(tmp_path: Path) -> None:
    changelog_file = tmp_path / "CHANGELOG.md"
    release_md = "## [1.0.0] - 2026-09-11\n\n### 🚀 Features\n- initial release"

    updated = ChangelogUpdater.update_file(changelog_file, release_md)
    assert updated is True
    assert changelog_file.is_file()

    content = changelog_file.read_text(encoding="utf-8")
    assert "# Changelog" in content
    assert "## [1.0.0] - 2026-09-11" in content


def test_changelog_updater_prepending(tmp_path: Path) -> None:
    changelog_file = tmp_path / "CHANGELOG.md"
    initial_content = (
        "# Changelog\n\n"
        "Keep a Changelog format.\n\n"
        "## [1.0.0] - 2026-08-01\n\n"
        "### 🚀 Features\n- old feature\n"
    )
    changelog_file.write_text(initial_content, encoding="utf-8")

    new_release_md = "## [1.1.0] - 2026-09-11\n\n### 🚀 Features\n- new feature"

    updated = ChangelogUpdater.update_file(changelog_file, new_release_md)
    assert updated is True

    updated_content = changelog_file.read_text(encoding="utf-8")
    pos_new = updated_content.find("## [1.1.0]")
    pos_old = updated_content.find("## [1.0.0]")

    assert pos_new != -1
    assert pos_old != -1
    # Ensure new release comes before old release
    assert pos_new < pos_old
