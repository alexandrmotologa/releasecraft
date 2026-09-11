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

Once approved, ReleaseCraft prepends the formatted entry to `CHANGELOG.md`, bumps version numbers in project manifest files (`pyproject.toml`, `package.json`, `Cargo.toml`), creates an annotated git tag, pushes to origin, uploads release assets, and publishes the release directly to GitHub.

## Core capabilities

- **Commit history traversal**: Locates the latest valid SemVer tag (`vX.Y.Z` or `X.Y.Z`) or falls back to the initial repository commit to scan all unreleased changes.
- **Conventional commits parser**: Extracts type, scope, breaking changes markers (`!` or `BREAKING CHANGE:`), and footers from each commit message.
- **Semantic version calculator**: Computes the next version bump according to SemVer 2.0.0 rules (major for breaking changes, minor for features, patch for fixes).
- **Interactive terminal curation**: A Textual split-pane dashboard with commit toggles on the left, inline message editing (`e`), section reclassification (`m`), real-time search (`/`), and a live Markdown preview on the right.
- **Manifest synchronization**: Automatically updates version declarations across `pyproject.toml`, `package.json`, `Cargo.toml`, and `VERSION` files.
- **Git hooks**: Enforces Conventional Commits rules on `git commit` via `releasecraft hook install`.
- **Release asset attachments**: Resolves and uploads distribution archives or binary wheels to GitHub Releases, generating matching `SHA256SUMS` manifests.
- **Monorepo support**: Restricts commit traversal by path or conventional scope (`--path packages/cli --tag-prefix cli-`).
- **Release highlights**: Synthesizes breaking changes and primary features into an executive summary block.
- **Webhook dispatching**: Notifies Discord, Slack, or custom webhooks upon release publication.
- **Changelog updater**: Inserts the new release block beneath the top header in `CHANGELOG.md` while leaving previous release history intact.

## Screenshots

### Interactive Terminal Curation (TUI)

Maintainers can review unreleased commits, toggle items into release notes, edit subjects inline, and inspect rendered markdown in real time:

<p align="center">
  <img src="docs/images/tui_screenshot.png?raw=true" alt="ReleaseCraft Interactive TUI" width="960" />
</p>

### CLI Release Preview & Executive Highlights

Generate the next release summary with breaking changes, semantic version calculation, and key highlights before applying changes:

<p align="center">
  <img src="docs/images/cli_preview.png?raw=true" alt="ReleaseCraft Release Preview" width="960" />
</p>

### Conventional Commits Diagnostic Check

Inspect unreleased commits to ensure strict conformance with Conventional Commits specifications:

<p align="center">
  <img src="docs/images/cli_check.png?raw=true" alt="ReleaseCraft Commit Convention Check" width="960" />
</p>

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

To include an executive highlights block:

```bash
releasecraft preview --highlights
```

### 2. Install the Git commit-msg hook

Ensure all team members write valid Conventional Commits locally:

```bash
releasecraft hook install
```

When a developer runs `git commit`, ReleaseCraft checks the message format and rejects non-conforming messages before they enter the repository history.

### 3. Validate commit conventions

Check that all unreleased commits follow Conventional Commits formatting rules:

```bash
releasecraft check
```

### 4. Launch interactive release curation

Review and curate release notes in an interactive terminal user interface:

```bash
releasecraft release --interactive
```

Keyboard controls in the TUI:
- `Up` / `Down`: Navigate commit list
- `Space`: Toggle commit inclusion in the release notes
- `e`: Edit commit subject for the release notes
- `m`: Reclassify commit to a different type (feat, fix, breaking)
- `/`: Focus the search bar to filter commits by text
- `p`: Approve and publish release
- `q`: Cancel and exit

### 5. Automated release with assets and manifest bump

Run an automated release that bumps `pyproject.toml`, updates `CHANGELOG.md`, attaches distribution assets, and notifies a webhook:

```bash
releasecraft release \
  --assets "dist/*.whl" \
  --assets "dist/*.tar.gz" \
  --webhook "https://discord.com/api/webhooks/..." \
  --webhook-type discord
```

For monorepos, release a specific package independently:

```bash
releasecraft release --path packages/cli --tag-prefix cli-
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
│       ├── manifests/               # Version synchronization in pyproject.toml, package.json
│       ├── hooks/                   # commit-msg validator and installer
│       ├── parser/                  # Conventional commit and SemVer calculation
│       ├── changelog/               # Changelog generation and highlights synthesis
│       ├── publisher/               # Multi-forge client, asset uploader, webhooks
│       └── tui/                     # Interactive Textual interface
└── tests/
    ├── unit/                        # Isolated tests for parsing, math, and manifests
    └── integration/                 # End-to-end tests on temporary git repositories
```

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
