# Command line interface reference

ReleaseCraft provides commands to preview version increments, generate changelogs, lint unreleased commits, manage git hooks, and execute releases.

## releasecraft release

Analyzes git history, calculates the next semantic version, updates the changelog, bumps project manifest files, creates an annotated git tag, attaches release assets, and pushes to remote.

```bash
releasecraft release [OPTIONS] [REPO_PATH]
```

### Options

- `--interactive`, `-i`: Launches the Textual terminal interface to curate commits before publishing.
- `--dry-run`: Computes the version bump and prints the changelog without creating git tags or calling external APIs.
- `--bump [major|minor|patch|pre]`: Forces a specific version bump override instead of calculating it from commit history.
- `--prerelease [alpha|beta|rc]`: Creates a pre-release version tag (such as `1.2.0-rc.1`).
- `--bump-manifests / --no-bump-manifests`: Automatically synchronizes new versions into `pyproject.toml`, `package.json`, `Cargo.toml`, `composer.json`, `pubspec.yaml`, `setup.cfg`, `version.go`, and `VERSION` (default: true).
- `--v0 / --zero-semver`: Enables Zero-Ver mode where breaking changes bump minor (0.x -> 0.y) and features bump patch.
- `--provider [github|gitlab|gitea]`: Remote git forge provider for publishing releases (default: auto-detected from remote URL or token).
- `--assets PATH`, `-a PATH`: Glob pattern for distribution assets to attach to the release (e.g. `dist/*.whl`).
- `--generate-checksums / --no-checksums`: Generates a `SHA256SUMS` file alongside uploaded release assets (default: true).
- `--highlights / --no-highlights`: Includes an executive highlights lead block summarizing breaking changes and top features.
- `--path TEXT`: Restricts commit analysis to a specific directory (useful for monorepos).
- `--scope TEXT`: Restricts commit analysis to a specific Conventional Commits scope.
- `--tag-prefix TEXT`: Custom prefix for release tags (e.g. `cli-` produces `cli-v1.2.0`).
- `--webhook URL`: Webhook endpoint to notify on release completion.
- `--webhook-type [discord|slack|generic]`: Webhook payload format (default: `generic`).
- `--publish / --no-publish`: Controls whether to publish the release to GitHub (defaults to true if `GITHUB_TOKEN` is available).
- `--push / --no-push`: Controls whether to push the commit and tag to the git remote.
- `--remote TEXT`: Git remote name (default: `origin`).

## releasecraft preview

Calculates the next version bump and prints the generated markdown changelog to standard output.

```bash
releasecraft preview [OPTIONS] [REPO_PATH]
```

### Options

- `--json`: Outputs the release metadata and changelog as a structured JSON object.
- `--v0 / --zero-semver`: Enables Zero-Ver mode where breaking changes bump minor (0.x -> 0.y) and features bump patch.
- `--include-all`: Includes chore and refactor commits that are excluded by default.
- `--highlights / --no-highlights`: Includes executive highlights lead block.
- `--path TEXT`: Filters commits by directory path.
- `--scope TEXT`: Filters commits by scope.
- `--tag-prefix TEXT`: Filters tags and prefixes output with custom tag prefix.

## releasecraft check

Validates all unreleased commits between the latest tag and `HEAD` against Conventional Commits 1.0.0 rules.

```bash
releasecraft check [OPTIONS] [REPO_PATH]
```

### Options

- `--tag-prefix TEXT`: Tag prefix filter when locating previous release boundary.

## releasecraft changelog

Updates or generates `CHANGELOG.md` without tagging or pushing.

```bash
releasecraft changelog [OPTIONS] [REPO_PATH]
```

### Options

- `--output PATH`, `-o`: File path for the changelog (default: `CHANGELOG.md`).
- `--version TEXT`: Explicit version header to write.
- `--path TEXT`: Filter commits by directory path.
- `--highlights / --no-highlights`: Include executive highlights block.

## releasecraft hook

Manages Git repository hooks to ensure every commit adheres to Conventional Commits rules at commit time.

### Subcommands

```bash
# Install commit-msg hook
releasecraft hook install [REPO_PATH]

# Uninstall commit-msg hook
releasecraft hook uninstall [REPO_PATH]

# Validate commit message file directly (invoked by hook)
releasecraft hook check-msg <COMMIT_MSG_FILE>
```

## releasecraft init

Initializes ReleaseCraft in the current repository by creating a default `.releasecraft.yaml` configuration file and optionally installing git commit-msg hooks.

```bash
releasecraft init [OPTIONS] [REPO_PATH]
```

### Options

- `--hooks / --no-hooks`: Automatically installs git `commit-msg` hook (default: true).
- `--force / --no-force`: Overwrites existing `.releasecraft.yaml` if already present.

