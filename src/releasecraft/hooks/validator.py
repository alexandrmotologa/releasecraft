"""Validator for Conventional Commits message format."""

import re
from pathlib import Path

CONVENTIONAL_COMMIT_REGEX = re.compile(
    r"^(?P<type>[a-zA-Z0-9_-]+)(?:\((?P<scope>[^()\r\n]+)\))?(?P<breaking>!)?:\s*(?P<subject>[^\r\n]+)"
)

STANDARD_TYPES = {
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
    "security",
}


class CommitMsgValidator:
    """Validates commit messages against Conventional Commits 1.0.0."""

    @classmethod
    def validate_message(
        cls,
        message: str,
        allowed_types: set[str] | None = None,
        max_subject_length: int = 100,
    ) -> tuple[bool, str]:
        """Validate a commit message.

        Args:
            message: The commit message text.
            allowed_types: Optional set of allowed commit types.
            max_subject_length: Maximum allowed character length for the subject line.

        Returns:
            Tuple of (is_valid: bool, error_message: str).
        """
        valid_types = allowed_types or STANDARD_TYPES

        # Strip git comment lines
        clean_lines = [
            line.strip() for line in message.splitlines() if not line.strip().startswith("#")
        ]

        # Filter out leading/trailing empty lines
        non_empty = [line for line in clean_lines if line]
        if not non_empty:
            return False, "Commit message is empty."

        header = non_empty[0]

        # Allow git merge commits
        if header.startswith("Merge branch ") or header.startswith("Merge pull request "):
            return True, ""

        match = CONVENTIONAL_COMMIT_REGEX.match(header)
        if not match:
            example = "feat(parser): add support for multiline footers"
            return False, (
                f"Invalid commit header format: '{header}'\n"
                f"Expected Conventional Commit format: <type>(<scope>)!?: <subject>\n"
                f"Example: {example}"
            )

        c_type = match.group("type").lower()
        if c_type not in valid_types:
            types_str = ", ".join(sorted(valid_types))
            return False, (f"Unknown commit type '{c_type}'.\nAllowed types are: {types_str}")

        subject = match.group("subject").strip()
        if not subject:
            return False, "Commit subject cannot be empty."

        if len(header) > max_subject_length:
            return False, (
                f"Commit header is too long ({len(header)} chars). "
                f"Maximum recommended length is {max_subject_length} chars."
            )

        return True, ""

    @classmethod
    def validate_file(cls, file_path: Path | str) -> tuple[bool, str]:
        """Validate a commit message stored in a file (used by git commit-msg hook)."""
        path = Path(file_path)
        if not path.is_file():
            return False, f"File not found: {file_path}"

        content = path.read_text(encoding="utf-8")
        return cls.validate_message(content)
