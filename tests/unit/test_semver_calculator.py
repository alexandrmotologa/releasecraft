"""Unit tests for SemVer calculation logic."""

from datetime import UTC, datetime

from releasecraft.models import BumpType, RawCommit, SemVerInfo
from releasecraft.parser.commit_parser import CommitParser
from releasecraft.parser.semver_calculator import SemVerCalculator


def make_parsed(message: str) -> CommitParser:
    raw = RawCommit(
        hash="abcdef1234567890abcdef1234567890abcdef12",
        short_hash="abcdef1",
        author_name="Dev",
        author_email="dev@example.com",
        timestamp=datetime.now(UTC),
        message=message,
    )
    return CommitParser.parse(raw)


def test_breaking_change_triggers_major() -> None:
    commits = [
        make_parsed("feat: add dashboard"),
        make_parsed("feat!: drop python 3.10 support"),
        make_parsed("fix: fix memory leak"),
    ]
    current = SemVerInfo(major=1, minor=4, patch=2)
    next_ver, bump = SemVerCalculator.calculate_next_version(current, commits)

    assert bump == BumpType.MAJOR
    assert str(next_ver) == "2.0.0"


def test_feat_triggers_minor() -> None:
    commits = [
        make_parsed("feat: add dark mode support"),
        make_parsed("fix: fix button alignment"),
    ]
    current = SemVerInfo(major=1, minor=4, patch=2)
    next_ver, bump = SemVerCalculator.calculate_next_version(current, commits)

    assert bump == BumpType.MINOR
    assert str(next_ver) == "1.5.0"


def test_fix_triggers_patch() -> None:
    commits = [
        make_parsed("fix: resolve null pointer exception"),
        make_parsed("perf: optimize regex lookup"),
    ]
    current = SemVerInfo(major=1, minor=4, patch=2)
    next_ver, bump = SemVerCalculator.calculate_next_version(current, commits)

    assert bump == BumpType.PATCH
    assert str(next_ver) == "1.4.3"


def test_prerelease_bump() -> None:
    commits = [make_parsed("feat: add webhook integration")]
    current = SemVerInfo(major=2, minor=0, patch=0)
    next_ver, bump = SemVerCalculator.calculate_next_version(
        current, commits, prerelease_token="rc"
    )

    assert bump == BumpType.PRERELEASE
    assert "2.1.0-rc.1" in str(next_ver) or "2.0.1-rc.1" in str(next_ver)


def test_initial_version_when_no_current() -> None:
    commits = [make_parsed("feat: initial commit")]
    next_ver, bump = SemVerCalculator.calculate_next_version(
        current_version=None,
        commits=commits,
        initial_version="0.1.0",
    )

    assert str(next_ver) == "0.1.0"
    assert bump == BumpType.PATCH
