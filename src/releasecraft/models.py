"""Domain models and data schemas for ReleaseCraft."""

from datetime import datetime
from enum import StrEnum
from typing import Any

import semver
from pydantic import BaseModel, Field


class BumpType(StrEnum):
    """Semantic version increment types."""

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PRERELEASE = "prerelease"
    NONE = "none"


class RawCommit(BaseModel):
    """Raw git commit representation directly from the repository."""

    hash: str
    short_hash: str
    author_name: str
    author_email: str
    timestamp: datetime
    message: str
    parent_hashes: list[str] = Field(default_factory=list)


class ParsedCommit(BaseModel):
    """Commit parsed and classified according to Conventional Commits 1.0.0."""

    raw: RawCommit
    type: str = "chore"
    scope: str | None = None
    subject: str = ""
    body: str | None = None
    footers: dict[str, str] = Field(default_factory=dict)
    is_breaking: bool = False
    breaking_description: str | None = None
    issue_refs: list[int] = Field(default_factory=list)
    included_in_release: bool = True

    @property
    def display_line(self) -> str:
        """Formatted single-line summary for changelog rendering."""
        scope_prefix = f"({self.scope}): " if self.scope else ": "
        return f"{self.type}{scope_prefix}{self.subject}"


class SemVerInfo(BaseModel):
    """Structured Semantic Version representation."""

    major: int = 0
    minor: int = 1
    patch: int = 0
    prerelease: str | None = None
    build: str | None = None

    @classmethod
    def from_string(cls, version_str: str) -> "SemVerInfo":
        """Parse a version string (stripping optional leading 'v') into SemVerInfo."""
        clean = version_str.strip().lstrip("v").lstrip("V")
        parsed = semver.Version.parse(clean)
        return cls(
            major=parsed.major,
            minor=parsed.minor,
            patch=parsed.patch,
            prerelease=parsed.prerelease,
            build=parsed.build,
        )

    def to_version(self) -> semver.Version:
        """Convert to semver.Version object."""
        return semver.Version(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            prerelease=self.prerelease,
            build=self.build,
        )

    def __str__(self) -> str:
        return str(self.to_version())

    def format_tag(self, prefix: str = "v") -> str:
        """Format as a git tag (e.g. v1.2.0)."""
        return f"{prefix}{self}"


class ReleaseSection(BaseModel):
    """A logical grouping of commits in the generated changelog."""

    section_id: str
    title: str
    emoji: str
    commits: list[ParsedCommit] = Field(default_factory=list)
    hidden: bool = False


class ReleasePlan(BaseModel):
    """Full release calculation and execution plan."""

    current_version: SemVerInfo | None = None
    current_tag: str | None = None
    next_version: SemVerInfo
    next_tag: str
    bump_type: BumpType
    base_commit_hash: str
    head_commit_hash: str
    commits: list[ParsedCommit] = Field(default_factory=list)
    sections: list[ReleaseSection] = Field(default_factory=list)
    changelog_markdown: str = ""
    is_prerelease: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
