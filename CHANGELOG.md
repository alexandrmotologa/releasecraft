# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-10-01

### 🚀 Features
- **manifests:** add version synchronization for `composer.json`, `pubspec.yaml`, `setup.cfg`, and `version.go`
- **publisher:** support multi-forge release publishing for GitHub, GitLab, and Gitea
- **semver:** add `--v0` / `zero_semver` mode for pre-1.0 initial development cycles
- **cli:** add `init` command for configuration scaffolding and automated git hook installation
- **screenshots:** add unified high-resolution Chrome headless renderer with JetBrains Mono

### 🐛 Bug Fixes
- **tui:** reset `is_breaking` flag when reclassifying away from breaking and guard UI lifecycle
- **git:** filter unreachable semver tags from parallel unmerged branches via ancestry check
- **changelog:** prevent duplicate breaking features in standard sections and preserve `[Unreleased]` block
- **publisher:** use streaming I/O for asset uploads and verify git remote push errors

## [0.1.0] - 2026-09-11

### 🚀 Features
- initialize releasecraft project scaffolding, docs, and ci (`240e625`)
