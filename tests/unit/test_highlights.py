"""Unit tests for HighlightsSynthesizer."""

from datetime import UTC, datetime

from releasecraft.changelog.highlights import HighlightsSynthesizer
from releasecraft.models import RawCommit
from releasecraft.parser.commit_parser import CommitParser


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


def test_highlights_synthesizer() -> None:
    commits = [
        make_parsed("feat(auth)!: switch to asymmetric Ed25519 tokens"),
        make_parsed("feat(ui): add modern dark theme"),
        make_parsed("perf(cache): 10x faster TTL eviction"),
        make_parsed("chore: update build script"),
    ]

    block = HighlightsSynthesizer.synthesize(commits, max_items=3)

    assert "#### 🌟 Highlights" in block
    assert "**Breaking**: switch to asymmetric Ed25519 tokens" in block
    assert "**ui**: add modern dark theme" in block
    assert "*Performance* - **cache**: 10x faster TTL eviction" in block
    assert "update build script" not in block
