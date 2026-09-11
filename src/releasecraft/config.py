"""Configuration management for ReleaseCraft."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class SectionConfig(BaseModel):
    """Configuration for a changelog section."""

    type: str
    title: str
    emoji: str
    hidden: bool = False


DEFAULT_SECTIONS: list[SectionConfig] = [
    SectionConfig(type="breaking", title="Breaking Changes", emoji="⚠️", hidden=False),
    SectionConfig(type="feat", title="Features", emoji="🚀", hidden=False),
    SectionConfig(type="fix", title="Bug Fixes", emoji="🐛", hidden=False),
    SectionConfig(type="perf", title="Performance Improvements", emoji="⚡", hidden=False),
    SectionConfig(type="security", title="Security", emoji="🔒", hidden=False),
    SectionConfig(type="refactor", title="Refactoring", emoji="🔄", hidden=True),
    SectionConfig(type="docs", title="Documentation", emoji="📚", hidden=True),
    SectionConfig(type="chore", title="Maintenance", emoji="🔧", hidden=True),
    SectionConfig(type="test", title="Tests", emoji="🧪", hidden=True),
    SectionConfig(type="ci", title="Continuous Integration", emoji="👷", hidden=True),
    SectionConfig(type="build", title="Build System", emoji="📦", hidden=True),
]


class ReleaseCraftConfig(BaseModel):
    """Project-wide release and changelog configuration."""

    tag_format: str = "v{version}"
    changelog_path: str = "CHANGELOG.md"
    remote: str = "origin"
    default_branch: str = "main"
    initial_version: str = "0.1.0"
    sections: list[SectionConfig] = Field(default_factory=lambda: list(DEFAULT_SECTIONS))
    github_repo: str | None = None
    sign_tag: bool = False
    extra: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def load(cls, repo_root: Path | str | None = None) -> "ReleaseCraftConfig":
        """Load configuration from .releasecraft.yaml / .releasecraft.yml or return defaults."""
        if repo_root is None:
            repo_root = Path.cwd()
        else:
            repo_root = Path(repo_root)

        for filename in [".releasecraft.yaml", ".releasecraft.yml"]:
            config_file = repo_root / filename
            if config_file.is_file():
                try:
                    with open(config_file, encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                    return cls(**data)
                except Exception:
                    # Fallback to default if configuration file parsing fails
                    return cls()

        return cls()
