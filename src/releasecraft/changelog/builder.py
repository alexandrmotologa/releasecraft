"""Changelog builder compiles commits into structured Markdown sections."""

from releasecraft.changelog.templates import ChangelogTemplate
from releasecraft.config import ReleaseCraftConfig
from releasecraft.models import ParsedCommit, ReleaseSection, SemVerInfo
from releasecraft.parser.pr_enricher import PREnricher


class ChangelogBuilder:
    """Organizes parsed commits and formats them into release notes."""

    def __init__(
        self,
        config: ReleaseCraftConfig | None = None,
        github_repo: str | None = None,
    ) -> None:
        self.config = config or ReleaseCraftConfig()
        repo = github_repo or self.config.github_repo
        self.enricher = PREnricher(github_repo=repo)

    def group_commits(
        self,
        commits: list[ParsedCommit],
        include_hidden: bool = False,
    ) -> list[ReleaseSection]:
        """Group active commits into configured release sections."""
        active = [c for c in commits if c.included_in_release]

        # Breaking changes section
        breaking_commits = [c for c in active if c.is_breaking]

        sections: list[ReleaseSection] = []

        # 1. Breaking changes first if any exist
        if breaking_commits:
            sections.append(
                ReleaseSection(
                    section_id="breaking",
                    title="Breaking Changes",
                    emoji="⚠️",
                    commits=breaking_commits,
                    hidden=False,
                )
            )

        # 2. Configured standard sections
        for sec in self.config.sections:
            if sec.type == "breaking":
                continue

            sec_commits = [
                c
                for c in active
                if c.type.lower() == sec.type.lower() and not (c.is_breaking and sec.type != "feat")
            ]

            if sec_commits:
                is_hidden = sec.hidden and not include_hidden
                sections.append(
                    ReleaseSection(
                        section_id=sec.type,
                        title=sec.title,
                        emoji=sec.emoji,
                        commits=sec_commits,
                        hidden=is_hidden,
                    )
                )

        # 3. Catch-all for uncategorized commit types (if not in config sections)
        known_types = {s.type.lower() for s in self.config.sections}
        known_types.add("breaking")

        other_commits = [
            c for c in active if c.type.lower() not in known_types and not c.is_breaking
        ]
        if other_commits and include_hidden:
            sections.append(
                ReleaseSection(
                    section_id="other",
                    title="Other Changes",
                    emoji="📋",
                    commits=other_commits,
                    hidden=False,
                )
            )

        return sections

    def build_markdown(
        self,
        version: SemVerInfo,
        commits: list[ParsedCommit],
        prev_version: SemVerInfo | None = None,
        date_str: str | None = None,
        include_hidden: bool = False,
        include_highlights: bool = False,
    ) -> tuple[str, list[ReleaseSection]]:
        """Generate release notes block in Markdown format.

        Returns:
            Tuple of (rendered_markdown: str, sections: list[ReleaseSection]).
        """
        sections = self.group_commits(commits, include_hidden=include_hidden)
        lines: list[str] = []

        # Version header
        header = ChangelogTemplate.render_version_header(
            version=version,
            date_str=date_str,
            github_repo=self.enricher.github_repo,
            prev_version=prev_version,
        )
        lines.append(header)
        lines.append("")

        # Optional executive highlights
        if include_highlights:
            from releasecraft.changelog.highlights import HighlightsSynthesizer

            highlights_block = HighlightsSynthesizer.synthesize(commits)
            if highlights_block:
                lines.append(highlights_block.strip())
                lines.append("")

        visible_sections = [s for s in sections if not s.hidden]
        if not visible_sections:
            lines.append("*No notable user-facing changes.*")
            lines.append("")
            return "\n".join(lines).strip(), sections

        for sec in visible_sections:
            if not sec.commits:
                continue

            sec_header = ChangelogTemplate.render_section_header(sec.title, sec.emoji)
            lines.append(sec_header)

            for commit in sec.commits:
                item_line = ChangelogTemplate.render_commit_item(
                    commit,
                    enricher=self.enricher,
                    include_hash=True,
                )
                lines.append(item_line)

            lines.append("")

        return "\n".join(lines).strip(), sections
