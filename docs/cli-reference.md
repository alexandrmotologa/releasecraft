# Command line interface reference

ReleaseCraft provides commands to preview version increments, generate changelogs, lint unreleased commits, and execute releases.

## releasecraft release

Analyzes git history, calculates the next semantic version, updates the changelog, creates an annotated git tag, and pushes to remote.

```bash
releasecraft release [OPTIONS] [REPO_PATH]
```

### Options

- `--interactive`, `-i`: Launches the Textual terminal interface to curate commits before publishing.
- `--dry-run`: Computes the version bump and prints the changelog without creating git tags or calling external APIs.
- `--bump [major|minor|patch|pre]`: Forces a specific version bump override instead of calculating it from commit history.
- `--prerelease [alpha|beta|rc]`: Creates a pre-release version tag (such as `1.2.0-rc.1`).
- `--publish / --no-publish`: Controls whether to publish the release to GitHub (defaults to true if `GITHUB_TOKEN` is available).
- `--push / --no-push`: Controls whether to push the commit and tag to the git remote.
- `--remote TEXT`: Git remote name (default: `origin`).
- `--branch TEXT`: Git branch name (default: current checked-out branch).

## releasecraft preview

Calculates the next version bump and prints the generated markdown changelog to standard output.

```bash
releasecraft preview [OPTIONS] [REPO_PATH]
```

### Options

- `--json`: Outputs the release metadata and changelog as a structured JSON object.
- `--include-all`: Includes chore and refactor commits that are excluded by default.

## releasecraft check

Validates all unreleased commits between the latest tag and `HEAD` against Conventional Commits 1.0.0 rules.

```bash
releasecraft check [OPTIONS] [REPO_PATH]
```

Returns exit code 0 if all commits follow conventional rules. Returns exit code 1 if invalid commit headers or formatting issues are detected.

## releasecraft changelog

Updates or generates `CHANGELOG.md` without tagging or pushing.

```bash
releasecraft changelog [OPTIONS] [REPO_PATH]
```

### Options

- `--output PATH`, `-o`: File path for the changelog (default: `CHANGELOG.md`).
- `--version TEXT`: Explicit version header to write.
- `--unreleased`: Generates an `## [Unreleased]` section.
