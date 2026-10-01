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


class WebhookConfig(BaseModel):
    """Configuration for a release announcement webhook."""

    url: str
    type: str = "generic"


class LinksConfig(BaseModel):
    """Link format templates for issues and commits."""

    github_repo: str | None = None
    issue_url: str | None = None
    commit_url: str | None = None


class ReleaseOptionsConfig(BaseModel):
    """Release execution options."""

    sign_tag: bool = False
    create_draft: bool = False
    prerelease: bool = False
    generate_checksums: bool = True
    assets: list[str] = Field(default_factory=list)


class ReleaseCraftConfig(BaseModel):
    """Project-wide release and changelog configuration."""

    tag_format: str = "v{version}"
    tag_prefix: str = ""
    changelog_path: str = "CHANGELOG.md"
    remote: str = "origin"
    default_branch: str = "main"
    initial_version: str = "0.1.0"
    bump_manifests: bool = True
    zero_semver: bool = False
    provider: str = "auto"
    sections: list[SectionConfig] = Field(default_factory=lambda: list(DEFAULT_SECTIONS))
    github_repo: str | None = None
    sign_tag: bool = False
    links: LinksConfig = Field(default_factory=LinksConfig)
    webhooks: list[WebhookConfig] = Field(default_factory=list)
    release: ReleaseOptionsConfig = Field(default_factory=ReleaseOptionsConfig)
    manifest_patterns: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """Harmonize backward-compatible configuration fields."""
        if not self.github_repo and self.links.github_repo:
            self.github_repo = self.links.github_repo
        if self.release.sign_tag:
            self.sign_tag = True

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
