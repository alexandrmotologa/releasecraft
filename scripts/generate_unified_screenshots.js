const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const OUTPUT_DIR = path.resolve(__dirname, '../docs/images');

if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// Shared theme & layout styles
const SHARED_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');

  :root {
    --bg-page: #070a0f;
    --bg-window: #0d1117;
    --bg-card: #161b22;
    --bg-surface: #0e131b;
    --border-window: rgba(255, 255, 255, 0.14);
    --border-card: rgba(255, 255, 255, 0.08);
    --text-primary: #e6edf3;
    --text-secondary: #8b949e;
    --text-muted: #6e7681;
    --accent-blue: #58a6ff;
    --accent-cyan: #39c5bb;
    --accent-green: #3fb950;
    --accent-yellow: #d29922;
    --accent-purple: #bc8cff;
    --accent-red: #f85149;
    --accent-magenta: #f778ba;
    --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }

  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  html, body {
    width: 100%;
    height: 100%;
    overflow: hidden;
  }

  body {
    background: var(--bg-page);
    font-family: var(--font-mono);
    color: var(--text-primary);
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 28px;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  .window {
    width: 100%;
    max-width: 1220px;
    background: var(--bg-window);
    border-radius: 12px;
    border: 1px solid var(--border-window);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(255, 255, 255, 0.05);
    overflow: hidden;
  }

  .window-header {
    height: 44px;
    background: #161b22;
    border-bottom: 1px solid var(--border-window);
    display: flex;
    align-items: center;
    padding: 0 16px;
    position: relative;
    user-select: none;
  }

  .traffic-lights {
    display: flex;
    gap: 8px;
  }

  .light {
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }

  .light-close { background: #ff5f56; box-shadow: 0 0 4px rgba(255, 95, 86, 0.4); }
  .light-min { background: #ffbd2e; box-shadow: 0 0 4px rgba(255, 189, 46, 0.4); }
  .light-max { background: #27c93f; box-shadow: 0 0 4px rgba(39, 201, 63, 0.4); }

  .window-title {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    font-family: var(--font-sans);
    font-size: 13px;
    font-weight: 600;
    color: var(--text-secondary);
    letter-spacing: -0.01em;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .window-title .highlight {
    color: var(--text-primary);
  }

  .window-body {
    padding: 24px;
    font-size: 14px;
    line-height: 1.6;
  }

  /* Shared badges & tags */
  .badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
    line-height: 1.2;
  }
  .badge-feat { background: rgba(57, 197, 187, 0.15); color: #39c5bb; border: 1px solid rgba(57, 197, 187, 0.3); }
  .badge-fix { background: rgba(88, 166, 255, 0.15); color: #58a6ff; border: 1px solid rgba(88, 166, 255, 0.3); }
  .badge-perf { background: rgba(188, 140, 255, 0.15); color: #bc8cff; border: 1px solid rgba(188, 140, 255, 0.3); }
  .badge-docs { background: rgba(210, 153, 34, 0.15); color: #d29922; border: 1px solid rgba(210, 153, 34, 0.3); }
  .badge-breaking { background: rgba(248, 81, 73, 0.2); color: #ff7b72; border: 1px solid rgba(248, 81, 73, 0.4); font-weight: 700; }
  .badge-major { background: rgba(248, 81, 73, 0.2); color: #ff7b72; font-weight: 700; }
  .badge-minor { background: rgba(57, 197, 187, 0.2); color: #39c5bb; font-weight: 700; }
  .badge-patch { background: rgba(88, 166, 255, 0.2); color: #58a6ff; font-weight: 700; }
`;

// 1. TUI Screen HTML
const TUI_HTML = `
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
${SHARED_CSS}

.tui-topbar {
  background: #111620;
  border: 1px solid var(--border-card);
  border-radius: 8px;
  padding: 10px 16px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.tui-topbar .title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}
.tui-topbar .app-name {
  font-weight: 700;
  color: var(--text-primary);
}
.tui-topbar .version-step {
  color: var(--text-secondary);
}
.tui-topbar .version-step strong {
  color: var(--accent-green);
}
.tui-topbar .version-tag {
  color: var(--accent-red);
  font-weight: 700;
}

.tui-grid {
  display: grid;
  grid-template-columns: 1fr 1.15fr;
  gap: 16px;
  min-height: 520px;
}

.tui-pane {
  background: var(--bg-surface);
  border: 1px solid var(--border-card);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.pane-header {
  background: #131924;
  border-bottom: 1px solid var(--border-card);
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 600;
  color: var(--accent-cyan);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pane-header span.hint {
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 400;
}

.search-bar {
  margin: 10px 12px 6px 12px;
  background: #090d14;
  border: 1px solid rgba(57, 197, 187, 0.3);
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 12px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 8px;
}
.search-bar .cursor {
  display: inline-block;
  width: 7px;
  height: 13px;
  background: var(--accent-cyan);
  animation: blink 1s step-end infinite;
}

.commit-list {
  padding: 8px 12px;
  overflow-y: hidden;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.commit-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px;
  border-radius: 6px;
  font-size: 12.5px;
  background: #0d121c;
  border: 1px solid transparent;
  transition: all 0.15s ease;
}

.commit-item.selected {
  background: rgba(88, 166, 255, 0.08);
  border-color: rgba(88, 166, 255, 0.3);
}

.commit-item.focused {
  background: #151f30;
  border-color: var(--accent-blue);
  box-shadow: 0 0 8px rgba(88, 166, 255, 0.2);
}

.commit-check {
  color: var(--accent-cyan);
  font-weight: 700;
  font-size: 12px;
}

.commit-hash {
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 12px;
}

.commit-type {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 1px 6px;
  border-radius: 3px;
  width: 58px;
  text-align: center;
}
.type-feat { background: rgba(57, 197, 187, 0.15); color: #39c5bb; }
.type-fix { background: rgba(88, 166, 255, 0.15); color: #58a6ff; }
.type-perf { background: rgba(188, 140, 255, 0.15); color: #bc8cff; }
.type-breaking { background: rgba(248, 81, 73, 0.2); color: #ff7b72; font-weight: 800; }

.commit-subject {
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

/* Markdown preview styling */
.preview-body {
  padding: 16px 20px;
  font-size: 13px;
  line-height: 1.65;
  color: var(--text-primary);
}

.preview-body h2 {
  font-size: 16px;
  color: var(--accent-cyan);
  border-bottom: 1px solid var(--border-card);
  padding-bottom: 6px;
  margin-bottom: 14px;
}

.preview-body h3 {
  font-size: 13.5px;
  margin-top: 14px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.preview-body h3.breaking { color: var(--accent-red); }
.preview-body h3.features { color: var(--accent-cyan); }
.preview-body h3.fixes { color: var(--accent-blue); }
.preview-body h3.perf { color: var(--accent-purple); }

.preview-body ul {
  list-style: none;
  padding-left: 4px;
}

.preview-body li {
  margin-bottom: 6px;
  padding-left: 14px;
  position: relative;
  font-size: 12.5px;
}

.preview-body li::before {
  content: "•";
  position: absolute;
  left: 0;
  color: var(--text-muted);
}

.preview-body .scope {
  color: var(--accent-purple);
  font-weight: 600;
}
.preview-body .hash {
  color: var(--accent-blue);
  font-size: 11.5px;
  text-decoration: underline;
}
.preview-body .breaking-desc {
  display: block;
  font-style: italic;
  color: var(--text-secondary);
  font-size: 11.5px;
  margin-top: 2px;
  padding-left: 6px;
  border-left: 2px solid rgba(248, 81, 73, 0.4);
}

.tui-footer {
  background: #111620;
  border: 1px solid var(--border-card);
  border-radius: 8px;
  padding: 8px 14px;
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.keybind-group {
  display: flex;
  gap: 16px;
}

.keybind {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
}

.key-badge {
  background: #21262d;
  color: var(--accent-cyan);
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 11px;
}
</style>
</head>
<body>
  <div class="window">
    <div class="window-header">
      <div class="traffic-lights">
        <div class="light light-close"></div>
        <div class="light light-min"></div>
        <div class="light light-max"></div>
      </div>
      <div class="window-title">
        <span>releasecraft release <span class="highlight">--interactive</span></span>
      </div>
    </div>
    <div class="window-body">
      <div class="tui-topbar">
        <div class="title-group">
          <span class="app-name">ReleaseCraft</span>
          <span class="version-step">Current: <strong>v1.1.0</strong> ➔ Proposed: <strong>v2.0.0</strong></span>
        </div>
        <span class="badge badge-breaking">MAJOR BUMP</span>
      </div>

      <div class="tui-grid">
        <!-- Left Pane: Commit Curator -->
        <div class="tui-pane">
          <div class="pane-header">
            <span>Commit Curator</span>
            <span class="hint">Space: toggle | e: edit | m: reclassify</span>
          </div>

          <div class="search-bar">
            <span style="color: var(--accent-cyan)">/</span>
            <span>Filter commits...</span>
            <span class="cursor"></span>
          </div>

          <div class="commit-list">
            <div class="commit-item selected focused">
              <span class="commit-check">[✓]</span>
              <span class="commit-hash">2e3f4a5</span>
              <span class="commit-type type-breaking">BREAK</span>
              <span class="commit-subject">(api)!: transition to unified multi-forge release provider pipeline</span>
            </div>
            <div class="commit-item selected">
              <span class="commit-check">[✓]</span>
              <span class="commit-hash">7a8b9c0</span>
              <span class="commit-type type-feat">FEAT</span>
              <span class="commit-subject">(manifest): support composer, pubspec, setup.cfg, and version.go</span>
            </div>
            <div class="commit-item selected">
              <span class="commit-check">[✓]</span>
              <span class="commit-hash">1c2d3e4</span>
              <span class="commit-type type-feat">FEAT</span>
              <span class="commit-subject">(cli): add init command for config scaffolding and git hook setup</span>
            </div>
            <div class="commit-item selected">
              <span class="commit-check">[✓]</span>
              <span class="commit-hash">5f6a7b8</span>
              <span class="commit-type type-feat">FEAT</span>
              <span class="commit-subject">(semver): support zero-semver v0 mode for initial iterations</span>
            </div>
            <div class="commit-item selected">
              <span class="commit-check">[✓]</span>
              <span class="commit-hash">9d0e1f2</span>
              <span class="commit-type type-feat">FEAT</span>
              <span class="commit-subject">(publisher): multi-forge release publishing for GitHub, GitLab, Gitea</span>
            </div>
            <div class="commit-item selected">
              <span class="commit-check">[✓]</span>
              <span class="commit-hash">3b4c5d6</span>
              <span class="commit-type type-perf">PERF</span>
              <span class="commit-subject">(scanner): verify branch ancestry to filter unreachable semver tags</span>
            </div>
            <div class="commit-item selected">
              <span class="commit-check">[✓]</span>
              <span class="commit-hash">8e9f0a1</span>
              <span class="commit-type type-fix">FIX</span>
              <span class="commit-subject">(tui): reset breaking flag on reclassification and guard UI lifecycle</span>
            </div>
            <div class="commit-item selected">
              <span class="commit-check">[✓]</span>
              <span class="commit-hash">4a5b6c7</span>
              <span class="commit-type type-fix">FIX</span>
              <span class="commit-subject">(changelog): prevent duplicate breaking feats and preserve unreleased</span>
            </div>
          </div>
        </div>

        <!-- Right Pane: Live Preview -->
        <div class="tui-pane">
          <div class="pane-header">
            <span>Live Changelog Preview</span>
            <span class="hint">Auto-rendered Markdown</span>
          </div>
          <div class="preview-body">
            <h2>[2.0.0] - 2026-10-01</h2>

            <h3 class="breaking">⚠️ Breaking Changes</h3>
            <ul>
              <li>
                <span class="scope">api:</span> transition to unified multi-forge release provider pipeline (<span class="hash">#2e3f4a5</span>)
                <span class="breaking-desc">BREAKING: Synchronous publisher functions are deprecated in favor of unified ReleaseProvider handlers.</span>
              </li>
            </ul>

            <h3 class="features">🚀 Features</h3>
            <ul>
              <li><span class="scope">manifest:</span> support composer, pubspec, setup.cfg, and version.go (<span class="hash">#7a8b9c0</span>)</li>
              <li><span class="scope">cli:</span> add init command for configuration scaffolding and git hook setup (<span class="hash">#1c2d3e4</span>)</li>
              <li><span class="scope">semver:</span> support zero-semver v0 mode for initial development (<span class="hash">#5f6a7b8</span>)</li>
              <li><span class="scope">publisher:</span> multi-forge release publishing for GitHub, GitLab, Gitea (<span class="hash">#9d0e1f2</span>)</li>
            </ul>

            <h3 class="fixes">🐛 Bug Fixes</h3>
            <ul>
              <li><span class="scope">tui:</span> reset breaking flag on reclassification and guard UI lifecycle (<span class="hash">#8e9f0a1</span>)</li>
              <li><span class="scope">changelog:</span> prevent duplicate breaking feats and preserve unreleased (<span class="hash">#4a5b6c7</span>)</li>
            </ul>

            <h3 class="perf">⚡ Performance Improvements</h3>
            <ul>
              <li><span class="scope">scanner:</span> verify branch ancestry to filter unreachable semver tags (<span class="hash">#3b4c5d6</span>)</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Footer Bar -->
      <div class="tui-footer">
        <div class="keybind-group">
          <div class="keybind"><span class="key-badge">p</span> <span>Approve & Publish</span></div>
          <div class="keybind"><span class="key-badge">e</span> <span>Edit Subject</span></div>
          <div class="keybind"><span class="key-badge">m</span> <span>Reclassify</span></div>
          <div class="keybind"><span class="key-badge">/</span> <span>Search</span></div>
          <div class="keybind"><span class="key-badge">a</span> <span>Toggle All</span></div>
        </div>
        <div class="keybind"><span class="key-badge">q</span> <span>Cancel & Quit</span></div>
      </div>
    </div>
  </div>
</body>
</html>
`;

// 2. CLI Preview Screen HTML
const PREVIEW_HTML = `
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
${SHARED_CSS}

.preview-summary-card {
  background: #111620;
  border: 1px solid rgba(57, 197, 187, 0.3);
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 24px;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.version-progression {
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.version-progression .current { color: var(--text-secondary); font-weight: 500; }
.version-progression .arrow { color: var(--accent-cyan); font-weight: 700; }
.version-progression .next { color: var(--accent-green); font-weight: 700; font-size: 17px; }

.meta-row {
  display: flex;
  gap: 20px;
  font-size: 12.5px;
  color: var(--text-secondary);
  border-top: 1px solid var(--border-card);
  padding-top: 10px;
}

.meta-item strong {
  color: var(--text-primary);
}

.highlights-card {
  background: rgba(188, 140, 255, 0.06);
  border: 1px solid rgba(188, 140, 255, 0.25);
  border-radius: 8px;
  padding: 14px 18px;
  margin-bottom: 24px;
}

.highlights-title {
  color: var(--accent-purple);
  font-size: 13.5px;
  font-weight: 700;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.highlights-list {
  list-style: none;
  font-size: 12.5px;
  color: var(--text-primary);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.highlights-list li::before {
  content: "✦";
  color: var(--accent-purple);
  margin-right: 8px;
}

.changelog-section {
  margin-top: 20px;
}

.changelog-title {
  font-size: 17px;
  color: var(--accent-cyan);
  border-bottom: 1px solid var(--border-card);
  padding-bottom: 6px;
  margin-bottom: 16px;
}

.section-group {
  margin-bottom: 16px;
}

.section-heading {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.section-heading.breaking { color: var(--accent-red); }
.section-heading.features { color: var(--accent-cyan); }
.section-heading.fixes { color: var(--accent-blue); }
.section-heading.perf { color: var(--accent-purple); }

.entry-list {
  list-style: none;
  padding-left: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.entry-item {
  font-size: 13px;
  display: flex;
  align-items: baseline;
  gap: 6px;
  position: relative;
  padding-left: 12px;
}

.entry-item::before {
  content: "•";
  position: absolute;
  left: 0;
  color: var(--text-muted);
}

.scope-tag {
  color: var(--accent-purple);
  font-weight: 600;
}
.commit-ref {
  color: var(--accent-blue);
  font-size: 12px;
  text-decoration: underline;
}
</style>
</head>
<body>
  <div class="window">
    <div class="window-header">
      <div class="traffic-lights">
        <div class="light light-close"></div>
        <div class="light light-min"></div>
        <div class="light light-max"></div>
      </div>
      <div class="window-title">
        <span>releasecraft preview <span class="highlight">--highlights</span></span>
      </div>
    </div>
    <div class="window-body">
      <!-- Summary Card -->
      <div class="preview-summary-card">
        <div class="summary-header">
          <div class="version-progression">
            <span class="current">Current: v1.1.0</span>
            <span class="arrow">➔</span>
            <span class="next">v2.0.0</span>
            <span class="badge badge-breaking">MAJOR BUMP</span>
          </div>
          <span style="font-size: 12.5px; color: var(--text-secondary)">8 unreleased commits analyzed</span>
        </div>
        <div class="meta-row">
          <div class="meta-item">Forge Provider: <strong>GitHub</strong> (alexandrmotologa/releasecraft)</div>
          <div class="meta-item">Manifests: <strong>pyproject.toml</strong>, <strong>package.json</strong>, <strong>composer.json</strong></div>
        </div>
      </div>

      <!-- Highlights Card -->
      <div class="highlights-card">
        <div class="highlights-title">✦ Executive Release Highlights</div>
        <ul class="highlights-list">
          <li><strong>Breaking:</strong> Synchronous publisher functions are deprecated in favor of unified ReleaseProvider handlers</li>
          <li><strong>manifest:</strong> Support composer.json, pubspec.yaml, setup.cfg, and version.go version synchronization</li>
          <li><strong>cli:</strong> Add init command for automated configuration scaffolding and git hook setup</li>
          <li><strong>semver:</strong> Support Zero-Ver v0 mode for initial development increments</li>
        </ul>
      </div>

      <!-- Rendered Changelog -->
      <div class="changelog-section">
        <div class="changelog-title">Changelog Preview: [2.0.0] - 2026-10-01</div>

        <div class="section-group">
          <div class="section-heading breaking">⚠️ Breaking Changes</div>
          <ul class="entry-list">
            <li class="entry-item">
              <span><span class="scope-tag">api:</span> transition to unified multi-forge release provider pipeline (<span class="commit-ref">#2e3f4a5</span>)</span>
            </li>
          </ul>
        </div>

        <div class="section-group">
          <div class="section-heading features">🚀 Features</div>
          <ul class="entry-list">
            <li class="entry-item"><span><span class="scope-tag">manifest:</span> support composer, pubspec, setup.cfg, and version.go manifests (<span class="commit-ref">#7a8b9c0</span>)</span></li>
            <li class="entry-item"><span><span class="scope-tag">cli:</span> add init command for configuration scaffolding and git hook setup (<span class="commit-ref">#1c2d3e4</span>)</span></li>
            <li class="entry-item"><span><span class="scope-tag">semver:</span> support zero-semver v0 mode for initial development iterations (<span class="commit-ref">#5f6a7b8</span>)</span></li>
            <li class="entry-item"><span><span class="scope-tag">publisher:</span> multi-forge release publishing for GitHub, GitLab, and Gitea (<span class="commit-ref">#9d0e1f2</span>)</span></li>
          </ul>
        </div>

        <div class="section-group">
          <div class="section-heading fixes">🐛 Bug Fixes</div>
          <ul class="entry-list">
            <li class="entry-item"><span><span class="scope-tag">tui:</span> reset breaking flag on reclassification and guard UI lifecycle (<span class="commit-ref">#8e9f0a1</span>)</span></li>
            <li class="entry-item"><span><span class="scope-tag">changelog:</span> prevent duplicate breaking feats and preserve unreleased block (<span class="commit-ref">#4a5b6c7</span>)</span></li>
          </ul>
        </div>

        <div class="section-group">
          <div class="section-heading perf">⚡ Performance Improvements</div>
          <ul class="entry-list">
            <li class="entry-item"><span><span class="scope-tag">scanner:</span> verify branch ancestry to filter unreachable semver tags (<span class="commit-ref">#3b4c5d6</span>)</span></li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
`;

// 3. CLI Check Screen HTML
const CHECK_HTML = `
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
${SHARED_CSS}

.check-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid var(--border-card);
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-surface);
  margin-bottom: 20px;
}

.check-table th {
  background: #131924;
  color: var(--accent-cyan);
  font-size: 12.5px;
  font-weight: 600;
  text-align: left;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-card);
}

.check-table td {
  padding: 8px 14px;
  font-size: 12.5px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
}

.check-table tr:last-child td {
  border-bottom: none;
}

.check-table tr:hover td {
  background: rgba(88, 166, 255, 0.04);
}

.col-hash { font-family: var(--font-mono); color: var(--text-muted); width: 90px; }
.col-type { width: 80px; }
.col-scope { color: var(--accent-purple); width: 110px; font-weight: 500; }
.col-break { width: 95px; }

.diagnostic-card {
  background: rgba(210, 153, 34, 0.08);
  border: 1px solid rgba(210, 153, 34, 0.3);
  border-radius: 8px;
  padding: 14px 18px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-primary);
}

.diagnostic-card .title {
  color: var(--accent-yellow);
  font-weight: 700;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.diagnostic-card strong {
  color: var(--accent-green);
}
.diagnostic-card .breaking-tag {
  color: var(--accent-red);
  font-weight: 700;
}
</style>
</head>
<body>
  <div class="window">
    <div class="window-header">
      <div class="traffic-lights">
        <div class="light light-close"></div>
        <div class="light light-min"></div>
        <div class="light light-max"></div>
      </div>
      <div class="window-title">
        <span>releasecraft check</span>
      </div>
    </div>
    <div class="window-body">
      <table class="check-table">
        <thead>
          <tr>
            <th class="col-hash">Hash</th>
            <th class="col-type">Type</th>
            <th class="col-scope">Scope</th>
            <th class="col-break">Breaking</th>
            <th>Commit Subject</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="col-hash">7a8b9c0</td>
            <td class="col-type"><span class="badge badge-feat">feat</span></td>
            <td class="col-scope">manifest</td>
            <td class="col-break"><span style="color: var(--text-muted)">No</span></td>
            <td>support composer, pubspec, setup.cfg, and version.go manifests</td>
          </tr>
          <tr>
            <td class="col-hash">1c2d3e4</td>
            <td class="col-type"><span class="badge badge-feat">feat</span></td>
            <td class="col-scope">cli</td>
            <td class="col-break"><span style="color: var(--text-muted)">No</span></td>
            <td>add init command for configuration scaffolding and git hook setup</td>
          </tr>
          <tr>
            <td class="col-hash">5f6a7b8</td>
            <td class="col-type"><span class="badge badge-feat">feat</span></td>
            <td class="col-scope">semver</td>
            <td class="col-break"><span style="color: var(--text-muted)">No</span></td>
            <td>support zero-semver v0 mode for initial development iterations</td>
          </tr>
          <tr>
            <td class="col-hash">9d0e1f2</td>
            <td class="col-type"><span class="badge badge-feat">feat</span></td>
            <td class="col-scope">publisher</td>
            <td class="col-break"><span style="color: var(--text-muted)">No</span></td>
            <td>multi-forge release publishing for GitHub, GitLab, and Gitea</td>
          </tr>
          <tr>
            <td class="col-hash">3b4c5d6</td>
            <td class="col-type"><span class="badge badge-perf">perf</span></td>
            <td class="col-scope">scanner</td>
            <td class="col-break"><span style="color: var(--text-muted)">No</span></td>
            <td>verify branch ancestry to filter unreachable semver tags</td>
          </tr>
          <tr>
            <td class="col-hash">8e9f0a1</td>
            <td class="col-type"><span class="badge badge-fix">fix</span></td>
            <td class="col-scope">tui</td>
            <td class="col-break"><span style="color: var(--text-muted)">No</span></td>
            <td>reset breaking flag on reclassification and guard UI lifecycle</td>
          </tr>
          <tr>
            <td class="col-hash">4a5b6c7</td>
            <td class="col-type"><span class="badge badge-fix">fix</span></td>
            <td class="col-scope">changelog</td>
            <td class="col-break"><span style="color: var(--text-muted)">No</span></td>
            <td>prevent duplicate breaking feats and preserve unreleased block</td>
          </tr>
          <tr>
            <td class="col-hash">2e3f4a5</td>
            <td class="col-type"><span class="badge badge-feat">feat</span></td>
            <td class="col-scope">api</td>
            <td class="col-break"><span class="badge badge-breaking">⚠️ YES</span></td>
            <td>transition to unified multi-forge release provider pipeline</td>
          </tr>
        </tbody>
      </table>

      <!-- Diagnostic Notice -->
      <div class="diagnostic-card">
        <div class="title">⚠️ Conventional Commits Diagnostic Report</div>
        <div>Breaking change detected in commit <code style="color: var(--accent-cyan)">2e3f4a5</code> (scope: <code style="color: var(--accent-purple)">api</code>).</div>
        <div>Calculated Semantic Versioning rule: <span class="breaking-tag">MAJOR</span> bump required (v1.1.0 ➔ <strong>v2.0.0</strong>).</div>
      </div>
    </div>
  </div>
</body>
</html>
`;

const screens = [
  { name: 'tui_screenshot', html: TUI_HTML, width: 1280, height: 860 },
  { name: 'cli_preview', html: PREVIEW_HTML, width: 1280, height: 860 },
  { name: 'cli_check', html: CHECK_HTML, width: 1280, height: 680 },
];

async function run() {
  const tmpDir = path.resolve(__dirname, '../.tmp_screens');
  if (!fs.existsSync(tmpDir)) fs.mkdirSync(tmpDir, { recursive: true });

  for (const screen of screens) {
    const htmlPath = path.join(tmpDir, `${screen.name}.html`);
    const pngPath = path.join(OUTPUT_DIR, `${screen.name}.png`);
    
    fs.writeFileSync(htmlPath, screen.html, 'utf-8');

    console.log(`[+] Rendering ${screen.name}.png via Chrome headless...`);
    const cmd = `"${CHROME_PATH}" --headless --disable-gpu --force-device-scale-factor=2 --window-size=${screen.width},${screen.height} --screenshot="${pngPath}" "${htmlPath}"`;
    execSync(cmd, { stdio: 'inherit' });
    console.log(`✓ Successfully generated ${screen.name}.png`);
  }

  // Cleanup
  fs.rmSync(tmpDir, { recursive: true, force: true });
  console.log('✓ All unified screenshots updated!');
}

run();
