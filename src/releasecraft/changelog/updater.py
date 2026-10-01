"""In-place updater for CHANGELOG.md files."""

import re
from pathlib import Path

CHANGELOG_PREAMBLE = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
"""

VERSION_HEADING_REGEX = re.compile(
    r"^##\s+\[(?P<version>(?!Unreleased\b)[^\]]+)\]",
    re.IGNORECASE | re.MULTILINE,
)
UNRELEASED_HEADING_REGEX = re.compile(
    r"^##\s+\[Unreleased\]",
    re.IGNORECASE | re.MULTILINE,
)


class ChangelogUpdater:
    """Updates or creates CHANGELOG.md files with new release blocks."""

    @classmethod
    def update_file(cls, file_path: Path | str, release_markdown: str) -> bool:
        """Insert a release block into a changelog file.

        Args:
            file_path: Path to CHANGELOG.md.
            release_markdown: Rendered Markdown block for the new release.

        Returns:
            True if file was updated, False if no change was needed.
        """
        path = Path(file_path)

        if not path.is_file():
            # Create fresh changelog file
            content = f"{CHANGELOG_PREAMBLE.strip()}\n\n{release_markdown.strip()}\n"
            path.write_text(content, encoding="utf-8")
            return True

        existing_content = path.read_text(encoding="utf-8")

        # Check if this exact release header is already present
        first_line = release_markdown.strip().splitlines()[0]
        if first_line in existing_content:
            # Already updated
            return False

        # Find the first release version section (excluding [Unreleased])
        match = VERSION_HEADING_REGEX.search(existing_content)

        if match:
            insert_pos = match.start()
            new_content = (
                existing_content[:insert_pos].rstrip()
                + "\n\n"
                + release_markdown.strip()
                + "\n\n"
                + existing_content[insert_pos:].lstrip()
            )
        else:
            # Check if there is an [Unreleased] header to insert below
            unreleased_match = UNRELEASED_HEADING_REGEX.search(existing_content)
            if unreleased_match:
                # Find end of the line containing ## [Unreleased]
                newline_pos = existing_content.find("\n", unreleased_match.end())
                insert_pos = newline_pos + 1 if newline_pos != -1 else len(existing_content)
                new_content = (
                    existing_content[:insert_pos].rstrip()
                    + "\n\n"
                    + release_markdown.strip()
                    + "\n\n"
                    + existing_content[insert_pos:].lstrip()
                )
            elif "# Changelog" in existing_content:
                header_pos = existing_content.find("# Changelog")
                # Find end of header line
                next_newline = existing_content.find("\n\n", header_pos)
                if next_newline != -1:
                    insert_pos = next_newline + 2
                    new_content = (
                        existing_content[:insert_pos]
                        + release_markdown.strip()
                        + "\n\n"
                        + existing_content[insert_pos:]
                    )
                else:
                    new_content = f"{existing_content.rstrip()}\n\n{release_markdown.strip()}\n"
            else:
                new_content = f"{CHANGELOG_PREAMBLE.strip()}\n\n{release_markdown.strip()}\n\n{existing_content.strip()}\n"

        path.write_text(new_content, encoding="utf-8")
        return True
