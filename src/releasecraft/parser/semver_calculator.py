"""Semantic version calculation engine based on Conventional Commits."""

from releasecraft.models import BumpType, ParsedCommit, SemVerInfo


class SemVerCalculator:
    """Calculates Semantic Version increments from parsed conventional commits."""

    @classmethod
    def determine_bump_type(cls, commits: list[ParsedCommit]) -> BumpType:
        """Analyze a collection of commits to determine the required SemVer bump.

        Rules:
            1. Any breaking change marker triggers a MAJOR increment.
            2. Any 'feat' commit triggers a MINOR increment.
            3. Fixes, performance improvements, security, and refactors trigger a PATCH increment.
            4. If no qualifying commits exist, returns BumpType.PATCH if commits exist, else BumpType.NONE.
        """
        active_commits = [c for c in commits if c.included_in_release]
        if not active_commits:
            return BumpType.NONE

        # Check for breaking changes
        if any(c.is_breaking for c in active_commits):
            return BumpType.MAJOR

        # Check for features
        if any(c.type == "feat" for c in active_commits):
            return BumpType.MINOR

        # Check for patch-level changes
        patch_types = {
            "fix",
            "perf",
            "security",
            "refactor",
            "docs",
            "chore",
            "style",
            "test",
            "build",
            "ci",
        }
        if any(c.type in patch_types for c in active_commits):
            return BumpType.PATCH

        return BumpType.PATCH

    @classmethod
    def calculate_next_version(
        cls,
        current_version: SemVerInfo | None,
        commits: list[ParsedCommit],
        bump_override: BumpType | None = None,
        prerelease_token: str | None = None,
        initial_version: str = "0.1.0",
    ) -> tuple[SemVerInfo, BumpType]:
        """Compute the next version according to SemVer 2.0.0 mathematics.

        Args:
            current_version: Current version, or None if no prior release tags exist.
            commits: List of parsed commits since last tag.
            bump_override: Optional explicit bump type override.
            prerelease_token: Optional pre-release identifier (e.g. 'rc', 'beta').
            initial_version: Fallback version string if no previous tags exist.

        Returns:
            Tuple of (next_version: SemVerInfo, bump_type: BumpType).
        """
        if current_version is None:
            # First release in the repository
            base = SemVerInfo.from_string(initial_version)
            bump = bump_override or BumpType.PATCH
            if prerelease_token:
                v = base.to_version().bump_prerelease(prerelease_token)
                return SemVerInfo.from_string(str(v)), BumpType.PRERELEASE
            return base, bump

        bump = bump_override or cls.determine_bump_type(commits)
        v = current_version.to_version()

        if bump == BumpType.MAJOR:
            next_v = v.bump_major()
        elif bump == BumpType.MINOR:
            next_v = v.bump_minor()
        elif bump == BumpType.PATCH:
            next_v = v.bump_patch()
        elif bump == BumpType.NONE:
            next_v = v
        else:
            next_v = v.bump_patch()

        if prerelease_token:
            next_v = next_v.bump_prerelease(token=prerelease_token)
            bump = BumpType.PRERELEASE

        result = SemVerInfo(
            major=next_v.major,
            minor=next_v.minor,
            patch=next_v.patch,
            prerelease=next_v.prerelease,
            build=next_v.build,
        )
        return result, bump
