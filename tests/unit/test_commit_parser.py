"""Unit tests for Conventional Commits parser."""

from datetime import UTC, datetime

from releasecraft.models import RawCommit
from releasecraft.parser.commit_parser import CommitParser


def create_raw(message: str) -> RawCommit:
    return RawCommit(
        hash="1234567890abcdef1234567890abcdef12345678",
        short_hash="1234567",
        author_name="Alex Motologa",
        author_email="alex@example.com",
        timestamp=datetime.now(UTC),
        message=message,
    )


def test_parse_simple_feature() -> None:
    raw = create_raw("feat: add database connection pool")
    parsed = CommitParser.parse(raw)

    assert parsed.type == "feat"
    assert parsed.scope is None
    assert parsed.subject == "add database connection pool"
    assert not parsed.is_breaking
    assert parsed.body is None


def test_parse_scoped_fix() -> None:
    raw = create_raw("fix(api): handle timeout when upstream is unreachable")
    parsed = CommitParser.parse(raw)

    assert parsed.type == "fix"
    assert parsed.scope == "api"
    assert parsed.subject == "handle timeout when upstream is unreachable"
    assert not parsed.is_breaking


def test_parse_breaking_change_exclamation() -> None:
    raw = create_raw("feat(auth)!: replace sessions with JWT tokens")
    parsed = CommitParser.parse(raw)

    assert parsed.type == "feat"
    assert parsed.scope == "auth"
    assert parsed.subject == "replace sessions with JWT tokens"
    assert parsed.is_breaking
    assert parsed.breaking_description == "replace sessions with JWT tokens"


def test_parse_breaking_change_footer() -> None:
    message = (
        "refactor(engine): overhaul execution pipeline\n\n"
        "Migrated from synchronous queue to asyncio event loops.\n\n"
        "BREAKING CHANGE: The run() method now returns an Awaitable instead of dict."
    )
    raw = create_raw(message)
    parsed = CommitParser.parse(raw)

    assert parsed.type == "refactor"
    assert parsed.scope == "engine"
    assert parsed.is_breaking
    assert (
        parsed.breaking_description == "The run() method now returns an Awaitable instead of dict."
    )
    assert "BREAKING CHANGE" in parsed.footers


def test_parse_issue_references() -> None:
    message = "fix(cli): parse boolean flags properly\n\nFixes #104, also relates to GH-208."
    raw = create_raw(message)
    parsed = CommitParser.parse(raw)

    assert parsed.issue_refs == [104, 208]


def test_parse_non_conventional_commit() -> None:
    raw = create_raw("updated README file and added quick start instructions")
    parsed = CommitParser.parse(raw)

    assert parsed.type == "chore"
    assert parsed.subject == "updated README file and added quick start instructions"
    assert not parsed.is_breaking
