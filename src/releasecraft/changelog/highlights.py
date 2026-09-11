"""Generates executive highlights and summaries for release notes."""

from releasecraft.models import ParsedCommit


class HighlightsSynthesizer:
    """Extracts and formats executive highlights for release announcements."""

    @classmethod
    def synthesize(
        cls,
        commits: list[ParsedCommit],
        max_items: int = 4,
    ) -> str:
        """Create a highlights block summarizing top changes.

        Args:
            commits: List of parsed commits for the release.
            max_items: Maximum number of bullet points to feature.

        Returns:
            Markdown block containing release highlights, or empty string if no qualifying commits.
        """
        active = [c for c in commits if c.included_in_release]
        if not active:
            return ""

        breaking = [c for c in active if c.is_breaking]
        features = [c for c in active if c.type == "feat" and not c.is_breaking]
        perf_and_sec = [c for c in active if c.type in ("perf", "security")]

        items: list[str] = []

        # 1. Breaking changes always come first
        for b in breaking:
            desc = b.breaking_description or b.subject
            items.append(f"**Breaking**: {desc}")
            if len(items) >= max_items:
                break

        # 2. Features
        if len(items) < max_items:
            for f in features:
                prefix = f"**{f.scope}**: " if f.scope else ""
                items.append(f"{prefix}{f.subject}")
                if len(items) >= max_items:
                    break

        # 3. Performance or Security
        if len(items) < max_items:
            for p in perf_and_sec:
                prefix = f"**{p.scope}**: " if p.scope else ""
                tag = "Performance" if p.type == "perf" else "Security"
                items.append(f"*{tag}* - {prefix}{p.subject}")
                if len(items) >= max_items:
                    break

        if not items:
            return ""

        bullet_lines = "\n".join(f"- {item}" for item in items)
        return f"#### 🌟 Highlights\n{bullet_lines}\n"
