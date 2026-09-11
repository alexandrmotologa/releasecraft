"""Unit tests for pull request and issue enricher."""

from datetime import UTC, datetime

from releasecraft.models import RawCommit
from releasecraft.parser.commit_parser import CommitParser
from releasecraft.parser.pr_enricher import PREnricher


def test_pr_enricher_without_repo() -> None:
    enricher = PREnricher(github_repo=None)
    raw = RawCommit(
        hash="abcdef1234567890abcdef1234567890abcdef12",
        short_hash="abcdef1",
        author_name="Dev",
        author_email="dev@example.com",
        timestamp=datetime.now(UTC),
        message="feat: add logging (#42)",
    )
    parsed = CommitParser.parse(raw)

    assert enricher.format_commit_hash(parsed) == "`abcdef1`"
    assert enricher.enrich_subject(parsed) == "add logging (#42)"


def test_pr_enricher_with_repo() -> None:
    enricher = PREnricher(github_repo="alexandrmotologa/releasecraft")
    raw = RawCommit(
        hash="abcdef1234567890abcdef1234567890abcdef12",
        short_hash="abcdef1",
        author_name="Dev",
        author_email="dev@example.com",
        timestamp=datetime.now(UTC),
        message="fix: resolve timeout (#42)",
    )
    parsed = CommitParser.parse(raw)

    assert (
        enricher.format_commit_hash(parsed)
        == "[`abcdef1`](https://github.com/alexandrmotologa/releasecraft/commit/abcdef1234567890abcdef1234567890abcdef12)"
    )
    assert (
        enricher.enrich_subject(parsed)
        == "resolve timeout ([#42](https://github.com/alexandrmotologa/releasecraft/issues/42))"
    )
