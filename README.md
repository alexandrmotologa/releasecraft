<p align="center">
  <img src="docs/images/logo.png?raw=true" alt="ReleaseCraft Logo" width="140" style="border-radius: 28px;" />
</p>

<h1 align="center">ReleaseCraft</h1>

<p align="center">
  <strong>Semantic Git release manager and changelog engine with interactive terminal review</strong>
</p>

<p align="center">
  <a href="https://github.com/alexandrmotologa/releasecraft/actions"><img src="https://img.shields.io/badge/CI-Passing-success?style=flat-square&logo=githubactions" alt="CI" /></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.12%2B-blue?style=flat-square&logo=python" alt="Python" /></a>
  <a href="https://semver.org/"><img src="https://img.shields.io/badge/SemVer-2.0.0-green?style=flat-square" alt="SemVer" /></a>
  <a href="https://www.conventionalcommits.org/"><img src="https://img.shields.io/badge/Conventional%20Commits-1.0.0-orange?style=flat-square" alt="Conventional Commits" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-teal?style=flat-square" alt="License" /></a>
</p>

ReleaseCraft is a local-first Git release manager. It analyzes commit history between the most recent version tag and the current working head, calculates the next semantic version according to Conventional Commits 1.0.0, and presents an interactive terminal interface where maintainers can curate release notes before committing them.

Once approved, ReleaseCraft prepends the formatted entry to `CHANGELOG.md`, creates an annotated git tag, pushes to origin, and publishes the release directly to GitHub.

## Core capabilities

- **Commit history traversal**: Locates the latest valid SemVer tag (`vX.Y.Z` or `X.Y.Z`) or falls back to the initial repository commit to scan all unreleased changes.
- **Conventional commits parser**: Extracts type, scope, breaking changes markers (`!` or `BREAKING CHANGE:`), and footers from each commit message.
- **Semantic version calculator**: Computes the next version bump according to SemVer 2.0.0 rules (major for breaking changes, minor for features, patch for fixes).
- **Interactive terminal curation**: A Textual split-pane dashboard with commit toggles on the left and a live Markdown preview on the right.
- **Changelog updater**: Inserts the new release block beneath the top header in `CHANGELOG.md` while leaving previous release history intact.
- **Pull request resolution**: Automatically extracts GitHub issue and pull request identifiers (`#42`) and links them in release notes.
- **GitHub release publishing**: Creates official GitHub releases via the REST API using an active `GITHUB_TOKEN` or your local `gh` session.
- **Commit linting**: Validates unreleased commits against Conventional Commits formatting rules with `releasecraft check`.

## Installation

### Prerequisites

- Python 3.12 or newer
- Git 2.30 or newer

### Install with uv (recommended)

```bash
uv tool install releasecraft
```

Or clone and install in editable mode:

```bash
git clone https://github.com/alexandrmotologa/releasecraft.git
cd releasecraft
uv venv
uv pip install -e ".[dev]"
```

Or install with pip:

```bash
pip install .
```

## Quick start

### 1. Preview the next release

Inspect unreleased commits and calculate the next version bump without modifying repository state:

```bash
releasecraft preview
```

Example output:

```text
Current version:  v1.4.2
Next version:     v1.5.0 (minor bump: 2 features, 3 fixes, 0 breaking)

### 🚀 Features
- (auth): add OAuth2 token refresh support (#58)
- (storage): support streaming uploads for large assets (#61)

### 🐛 Bug Fixes
- (db): resolve connection pool leak on timeout (#59)
- (cli): parse quoted flags correctly (#60)
- (cache): invalidate stale session keys (#63)
```

### 2. Validate commit conventions

Check that all unreleased commits follow Conventional Commits formatting rules:

```bash
releasecraft check
```

### 3. Launch interactive release curation

Review and curate release notes in an interactive terminal user interface:

```bash
releasecraft release --interactive
```

Keyboard controls in the TUI:
- `Up` / `Down`: Navigate commit list
- `Space`: Toggle commit inclusion in the release notes
- `p`: Approve and publish release
- `q`: Cancel and exit

### 4. Headless release in CI/CD

Run automated releases in continuous delivery pipelines:

```bash
releasecraft release --no-interactive
```

To run without pushing to remote or calling external APIs, use dry run mode:

```bash
releasecraft release --dry-run
```

## Project structure

```
releasecraft/
├── pyproject.toml                   # Build configuration and dependencies
├── Dockerfile                       # Minimal container for CI runners
├── src/
│   └── releasecraft/
│       ├── cli.py                   # Typer CLI application
│       ├── config.py                # Configuration loader (.releasecraft.yaml)
│       ├── models.py                # Pydantic schemas (Commit, Release, SemVer)
│       ├── git/                     # Git repository inspection and tagging
│       ├── parser/                  # Conventional commit and SemVer calculation
│       ├── changelog/               # Changelog generation and file updater
│       ├── publisher/               # GitHub API client and git push logic
│       └── tui/                     # Interactive Textual interface
└── tests/
    ├── unit/                        # Isolated tests for parsing and math
    └── integration/                 # End-to-end tests on temporary git repositories
```

## Configuration

Place an optional `.releasecraft.yaml` in your repository root to configure section headers, hidden commit types, and tag formats:

```yaml
tag_format: "v{version}"
changelog_path: "CHANGELOG.md"
remote: "origin"

sections:
  - type: "breaking"
    title: "Breaking Changes"
    emoji: "⚠️"
    hidden: false
  - type: "feat"
    title: "Features"
    emoji: "🚀"
    hidden: false
  - type: "fix"
    title: "Bug Fixes"
    emoji: "🐛"
    hidden: false
```

See [docs/configuration.md](docs/configuration.md) for full configuration options.

## Testing

Run the test suite with pytest:

```bash
uv run pytest
```

Check code formatting and linting with Ruff:

```bash
uv run ruff check src tests
uv run ruff format --check src tests
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
