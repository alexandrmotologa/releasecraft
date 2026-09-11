"""Enriches commits with pull request, issue, and author links."""

import re

from releasecraft.models import ParsedCommit

PR_ISSUE_PATTERN = re.compile(r"(?:#|GH-)(?P<id>[1-9]\d*)")


class PREnricher:
    """Enriches commit descriptions and summaries with GitHub reference links."""

    def __init__(self, github_repo: str | None = None) -> None:
        """Initialize PREnricher.

        Args:
            github_repo: Repository in 'owner/name' format (e.g. 'alexandrmotologa/releasecraft').
        """
        self.github_repo = github_repo.strip("/") if github_repo else None

    def format_commit_hash(self, commit: ParsedCommit) -> str:
        """Format a commit hash as a markdown link if repository is known."""
        short_hash = commit.raw.short_hash
        if not self.github_repo:
            return f"`{short_hash}`"
        url = f"https://github.com/{self.github_repo}/commit/{commit.raw.hash}"
        return f"[`{short_hash}`]({url})"

    def linkify_issues(self, text: str) -> str:
        """Replace '#42' or 'GH-42' occurrences with clickable markdown links."""
        if not self.github_repo:
            return text

        def _replace_match(match: re.Match) -> str:
            issue_id = match.group("id")
            url = f"https://github.com/{self.github_repo}/issues/{issue_id}"
            return f"[#{issue_id}]({url})"

        return PR_ISSUE_PATTERN.sub(_replace_match, text)

    def enrich_subject(self, commit: ParsedCommit) -> str:
        """Format the commit subject with linkified issue numbers."""
        return self.linkify_issues(commit.subject)
