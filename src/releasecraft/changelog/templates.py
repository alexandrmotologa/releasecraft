"""Markdown templates and formatters for Keep a Changelog."""

from datetime import UTC, datetime

from releasecraft.models import ParsedCommit, SemVerInfo
from releasecraft.parser.pr_enricher import PREnricher


class ChangelogTemplate:
    """Renders formatted Markdown elements for release notes."""

    @staticmethod
    def render_version_header(
        version: SemVerInfo,
        date_str: str | None = None,
        github_repo: str | None = None,
        prev_version: SemVerInfo | None = None,
        tag_template: str = "v{version}",
    ) -> str:
        """Render the H2 version header with date and optional comparison link."""
        if not date_str:
            date_str = datetime.now(UTC).strftime("%Y-%m-%d")

        v_str = str(version)
        if github_repo and prev_version:
            curr_tag = tag_template.format(version=str(version))
            prev_tag = tag_template.format(version=str(prev_version))
            compare_url = f"https://github.com/{github_repo}/compare/{prev_tag}...{curr_tag}"
            return f"## [{v_str}]({compare_url}) - {date_str}"

        return f"## [{v_str}] - {date_str}"

    @staticmethod
    def render_section_header(title: str, emoji: str = "") -> str:
        """Render an H3 section header."""
        prefix = f"{emoji} " if emoji else ""
        return f"### {prefix}{title}"

    @staticmethod
    def render_commit_item(
        commit: ParsedCommit,
        enricher: PREnricher | None = None,
        include_hash: bool = True,
    ) -> str:
        """Render a single bulleted commit line."""
        scope_str = f"**{commit.scope}**: " if commit.scope else ""
        subject = enricher.linkify_issues(commit.subject) if enricher else commit.subject
        hash_str = f" ({enricher.format_commit_hash(commit)})" if enricher and include_hash else ""

        line = f"- {scope_str}{subject}{hash_str}"

        # If breaking change has an extended description different from subject, add it
        if (
            commit.is_breaking
            and commit.breaking_description
            and commit.breaking_description != commit.subject
        ):
            line += f"\n  - *BREAKING*: {commit.breaking_description}"

        return line
