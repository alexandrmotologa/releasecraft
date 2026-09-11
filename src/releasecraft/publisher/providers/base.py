"""Abstract base class for Git forge release providers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ReleaseProvider(ABC):
    """Abstract interface for remote release services."""

    @abstractmethod
    def create_release(
        self,
        tag_name: str,
        name: str,
        body: str,
        target_commitish: str = "main",
        draft: bool = False,
        prerelease: bool = False,
        assets: list[Path] | None = None,
    ) -> dict[str, Any]:
        """Publish a release to the forge and return response metadata."""
        pass
