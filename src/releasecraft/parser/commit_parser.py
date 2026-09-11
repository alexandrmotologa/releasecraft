"""Conventional Commits 1.0.0 parser."""

import re

from releasecraft.models import ParsedCommit, RawCommit

# Regular expression matching: <type>(<scope>)!?: <subject>
CONVENTIONAL_HEADER_REGEX = re.compile(
    r"^(?P<type>[a-zA-Z0-9_-]+)(?:\((?P<scope>[^()\r\n]+)\))?(?P<breaking>!)?:\s*(?P<subject>[^\r\n]+)"
)

# Regular expression for footers: KEY: VALUE or KEY #VALUE
FOOTER_REGEX = re.compile(r"^(?P<key>[a-zA-Z0-9_-]+|BREAKING[ -]CHANGE)(?::|\s+#)\s*(?P<value>.+)$")

# Regular expression to extract issue/PR numbers: #42, GH-42
ISSUE_REF_REGEX = re.compile(r"(?:#|GH-)(?P<id>[1-9]\d*)")


class CommitParser:
    """Parses raw git commits into structured Conventional Commits objects."""

    @classmethod
    def parse(cls, raw: RawCommit) -> ParsedCommit:
        """Parse a RawCommit into a ParsedCommit."""
        lines = [line.rstrip() for line in raw.message.strip().splitlines()]
        if not lines:
            return ParsedCommit(
                raw=raw,
                type="chore",
                subject="",
                included_in_release=False,
            )

        header = lines[0]
        body_lines: list[str] = []
        footers: dict[str, str] = {}
        is_breaking = False
        breaking_description: str | None = None

        match = CONVENTIONAL_HEADER_REGEX.match(header)
        if match:
            commit_type = match.group("type").lower()
            scope = match.group("scope")
            if scope:
                scope = scope.strip()
            subject = match.group("subject").strip()
            if match.group("breaking"):
                is_breaking = True
                breaking_description = subject
        else:
            # Fallback for non-conventional commit messages
            commit_type = "chore"
            scope = None
            subject = header.strip()

        # Parse body and footers from remaining lines
        if len(lines) > 1:
            i = 1
            # Skip empty lines between header and body
            while i < len(lines) and not lines[i].strip():
                i += 1

            # Traverse paragraphs
            current_paragraph: list[str] = []
            paragraphs: list[list[str]] = []

            while i < len(lines):
                line = lines[i]
                if not line.strip():
                    if current_paragraph:
                        paragraphs.append(current_paragraph)
                        current_paragraph = []
                else:
                    current_paragraph.append(line)
                i += 1

            if current_paragraph:
                paragraphs.append(current_paragraph)

            # Check trailing paragraphs for footers
            for paragraph in paragraphs:
                joined_p = "\n".join(paragraph)
                footer_match = FOOTER_REGEX.match(paragraph[0])

                if footer_match:
                    key = footer_match.group("key")
                    # Value might span multiple indented lines
                    val = footer_match.group("value")
                    if len(paragraph) > 1:
                        val += "\n" + "\n".join(paragraph[1:])

                    norm_key = key.replace(" ", "-").upper()
                    if norm_key in ("BREAKING-CHANGE", "BREAKING_CHANGE"):
                        is_breaking = True
                        breaking_description = val.strip()

                    footers[key] = val.strip()
                elif joined_p.startswith("BREAKING CHANGE:") or joined_p.startswith(
                    "BREAKING-CHANGE:"
                ):
                    is_breaking = True
                    desc = joined_p.split(":", 1)[1].strip()
                    breaking_description = desc
                    footers["BREAKING CHANGE"] = desc
                else:
                    body_lines.append(joined_p)

        body = "\n\n".join(body_lines).strip() if body_lines else None

        # Extract issue references from full commit text
        issue_refs: list[int] = []
        for ref_match in ISSUE_REF_REGEX.finditer(raw.message):
            issue_id = int(ref_match.group("id"))
            if issue_id not in issue_refs:
                issue_refs.append(issue_id)

        return ParsedCommit(
            raw=raw,
            type=commit_type,
            scope=scope,
            subject=subject,
            body=body,
            footers=footers,
            is_breaking=is_breaking,
            breaking_description=breaking_description,
            issue_refs=issue_refs,
            included_in_release=True,
        )

    @classmethod
    def parse_many(cls, raw_commits: list[RawCommit]) -> list[ParsedCommit]:
        """Parse an iterable of RawCommits into ParsedCommits."""
        return [cls.parse(c) for c in raw_commits]
