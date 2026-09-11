# Configuration

ReleaseCraft looks for an optional configuration file named `.releasecraft.yaml` or `.releasecraft.yml` in the root directory of your git repository. If absent, default settings are applied.

## Configuration file schema

```yaml
# Version tag pattern. Default: "v{version}"
tag_format: "v{version}"

# Optional tag prefix (e.g. for monorepos: "cli-")
tag_prefix: ""

# Target changelog file path. Default: "CHANGELOG.md"
changelog_path: "CHANGELOG.md"

# Git remote name. Default: "origin"
remote: "origin"

# Automatically synchronize version in pyproject.toml, package.json, Cargo.toml
bump_manifests: true

# Conventional commit section definitions
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

  - type: "perf"
    title: "Performance Improvements"
    emoji: "⚡"
    hidden: false

  - type: "refactor"
    title: "Code Refactoring"
    emoji: "🔄"
    hidden: true

  - type: "docs"
    title: "Documentation"
    emoji: "📚"
    hidden: true

  - type: "chore"
    title: "Maintenance"
    emoji: "🔧"
    hidden: true

# Issue and pull request link templates
links:
  github_repo: "owner/repository"
  issue_url: "https://github.com/owner/repository/issues/{id}"
  commit_url: "https://github.com/owner/repository/commit/{hash}"

# Webhook announcements upon release
webhooks:
  - url: "https://discord.com/api/webhooks/..."
    type: "discord"
  - url: "https://hooks.slack.com/services/..."
    type: "slack"

# Release options
release:
  sign_tag: false
  create_draft: false
  prerelease: false
  generate_checksums: true
  assets:
    - "dist/*.whl"
    - "dist/*.tar.gz"
```

## Section visibility

By default, internal commits (`chore`, `test`, `refactor`, `style`) have `hidden: true` in public release notes to keep announcements focused on user-facing changes. Maintainers can toggle them back on during interactive review or by setting `hidden: false` in `.releasecraft.yaml`.
