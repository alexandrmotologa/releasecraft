"""Unit tests for Textual TUI interface."""

from datetime import UTC, datetime

import pytest

from releasecraft.changelog.builder import ChangelogBuilder
from releasecraft.models import RawCommit, SemVerInfo
from releasecraft.parser.commit_parser import CommitParser
from releasecraft.tui.app import ReleaseCraftApp
from releasecraft.tui.screens import EditCommitModal


def make_parsed_commit(message: str) -> CommitParser:
    raw = RawCommit(
        hash="abcdef1234567890abcdef1234567890abcdef12",
        short_hash="abcdef1",
        author_name="Dev",
        author_email="dev@example.com",
        timestamp=datetime.now(UTC),
        message=message,
    )
    return CommitParser.parse(raw)


@pytest.mark.asyncio
async def test_tui_app_mount_and_publish() -> None:
    commits = [
        make_parsed_commit("feat: add dashboard"),
        make_parsed_commit("fix: resolve crash"),
    ]
    current = SemVerInfo(major=1, minor=0, patch=0)
    builder = ChangelogBuilder()

    app = ReleaseCraftApp(
        current_version=current,
        commits=commits,
        builder=builder,
    )

    async with app.run_test() as pilot:
        assert app.next_version.major == 1
        assert app.next_version.minor == 1
        assert not app.confirmed

        # Press 'p' to publish
        await pilot.press("p")

    assert app.confirmed is True


@pytest.mark.asyncio
async def test_tui_app_filter_and_quit() -> None:
    commits = [
        make_parsed_commit("feat: add dashboard"),
        make_parsed_commit("fix: resolve crash"),
    ]
    current = SemVerInfo(major=1, minor=0, patch=0)
    builder = ChangelogBuilder()

    app = ReleaseCraftApp(
        current_version=current,
        commits=commits,
        builder=builder,
    )

    async with app.run_test() as pilot:
        # Test search filter
        app.search_input.value = "crash"
        await pilot.pause()
        assert len(app.selection_list._options) == 1

        # Clear filter
        app.search_input.value = ""
        await pilot.pause()
        assert len(app.selection_list._options) == 2

        await pilot.press("q")

    assert app.confirmed is False


@pytest.mark.asyncio
async def test_edit_commit_modal() -> None:
    modal = EditCommitModal("initial subject")
    assert modal.initial_text == "initial subject"


@pytest.mark.asyncio
async def test_reclassify_resets_is_breaking() -> None:
    commit = make_parsed_commit("feat!: breaking change")
    assert commit.is_breaking is True

    app = ReleaseCraftApp(
        current_version=SemVerInfo(major=1, minor=0, patch=0),
        commits=[commit],
        builder=ChangelogBuilder(),
    )
    async with app.run_test():
        assert app.next_version.major == 2

        # Reclassify to fix
        commit.is_breaking = False
        commit.type = "fix"
        app._refresh_state()

        assert commit.is_breaking is False
        assert str(app.next_version) == "1.0.1"
