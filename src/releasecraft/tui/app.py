"""Main Textual application for interactive release curation."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, Label, SelectionList
from textual.widgets.selection_list import Selection

from releasecraft.changelog.builder import ChangelogBuilder
from releasecraft.models import BumpType, ParsedCommit, SemVerInfo
from releasecraft.parser.semver_calculator import SemVerCalculator
from releasecraft.tui.screens import EditCommitModal, ReclassifyModal
from releasecraft.tui.widgets import ChangelogPreviewPane, SemVerHeader


class ReleaseCraftApp(App):
    """Interactive TUI for reviewing commits and previewing release notes."""

    CSS = """
    Screen {
        background: #0f172a;
        color: #f8fafc;
    }

    SemVerHeader {
        dock: top;
        height: 3;
        background: #1e293b;
        color: #f8fafc;
        content-align: center middle;
        border-bottom: solid #3b82f6;
    }

    #main-split {
        height: 1fr;
        padding: 1;
    }

    #left-pane {
        width: 1fr;
        border: solid #3b82f6;
        padding: 1;
        margin-right: 1;
    }

    #right-pane {
        width: 1fr;
        border: solid #6366f1;
        padding: 1;
    }

    #search-input {
        margin-bottom: 1;
        background: #0b0f19;
        color: #f8fafc;
        border: solid #334155;
    }

    SelectionList {
        height: 1fr;
        background: #0b0f19;
        border: solid #334155;
    }

    .pane-title {
        text-style: bold;
        color: #38bdf8;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("p", "publish", "Approve & Publish", priority=True),
        Binding("e", "edit_commit", "Edit Subject"),
        Binding("m", "reclassify_commit", "Reclassify"),
        Binding("slash", "focus_search", "Search (/)"),
        Binding("a", "toggle_all", "Toggle All"),
        Binding("q", "quit", "Cancel & Quit"),
    ]

    def __init__(
        self,
        current_version: SemVerInfo | None,
        commits: list[ParsedCommit],
        builder: ChangelogBuilder,
        initial_bump_type: BumpType = BumpType.PATCH,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.current_version = current_version
        self.commits = commits
        self.builder = builder
        self.bump_type = initial_bump_type
        self.confirmed = False
        self.active_filter = ""

        # Calculate initial version
        self.next_version, self.bump_type = SemVerCalculator.calculate_next_version(
            current_version=self.current_version,
            commits=self.commits,
        )

        initial_md, _ = self.builder.build_markdown(
            version=self.next_version,
            commits=self.commits,
            prev_version=self.current_version,
        )
        self.current_markdown = initial_md

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        self.header_widget = SemVerHeader(
            current_version=self.current_version,
            next_version=self.next_version,
            bump_type=self.bump_type,
            id="semver-header",
        )
        yield self.header_widget

        with Horizontal(id="main-split"):
            with Vertical(id="left-pane"):
                yield Label(
                    "Commit Curator (Space: toggle | e: edit | m: reclassify | /: search)",
                    classes="pane-title",
                )
                self.search_input = Input(
                    placeholder="Filter commits... (press '/' to focus)",
                    id="search-input",
                )
                yield self.search_input

                self.selection_list = SelectionList[int](id="commit-selector")
                yield self.selection_list
                self._populate_selections()

            with Vertical(id="right-pane"):
                self.preview_pane = ChangelogPreviewPane(
                    self.current_markdown,
                    id="changelog-preview",
                )
                yield self.preview_pane

        yield Footer()

    def _populate_selections(self) -> None:
        """Populate or update selection list items according to active filter."""
        self.selection_list.clear_options()
        query = self.active_filter.lower()

        for idx, c in enumerate(self.commits):
            text = f"[{c.raw.short_hash}] {c.type.upper()}: {c.subject}"
            if query and query not in text.lower():
                continue
            self.selection_list.add_option(
                Selection(text, idx, initial_state=c.included_in_release)
            )

    def on_mount(self) -> None:
        """Focus commit selection list by default so hotkeys take effect immediately."""
        self.selection_list.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter commit list when search query changes."""
        if event.input.id == "search-input":
            self.active_filter = event.value.strip()
            self._populate_selections()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """When Enter is pressed in search bar, return focus to selection list."""
        self.selection_list.focus()

    def on_selection_list_selected_changed(self, event: SelectionList.SelectedChanged) -> None:
        """Handle toggle of commits in the list."""
        selected_set = set(event.selection_list.selected)

        # Update included status for visible items
        for option in self.selection_list._options:
            commit_idx = option.value
            self.commits[commit_idx].included_in_release = commit_idx in selected_set

        self._refresh_state()

    def _refresh_state(self) -> None:
        """Recalculate version and update changelog preview."""
        self.next_version, self.bump_type = SemVerCalculator.calculate_next_version(
            current_version=self.current_version,
            commits=self.commits,
        )

        new_md, _ = self.builder.build_markdown(
            version=self.next_version,
            commits=self.commits,
            prev_version=self.current_version,
        )
        self.current_markdown = new_md

        if hasattr(self, "preview_pane"):
            self.preview_pane.update_content(new_md)
        if hasattr(self, "header_widget"):
            self.header_widget.current_version = self.current_version
            self.header_widget.next_version = self.next_version
            self.header_widget.bump_type = self.bump_type
            self.header_widget.refresh()

    def action_focus_search(self) -> None:
        """Focus the search filter input."""
        self.search_input.focus()

    def action_edit_commit(self) -> None:
        """Open modal dialog to edit the highlighted commit description."""
        if self.selection_list.highlighted is None:
            return

        commit_idx = self.selection_list.get_option_at_index(self.selection_list.highlighted).value
        commit = self.commits[commit_idx]

        def _on_edit_dismissed(new_subject: str | None) -> None:
            if new_subject:
                commit.subject = new_subject
                self._populate_selections()
                self._refresh_state()

        self.push_screen(EditCommitModal(initial_text=commit.subject), _on_edit_dismissed)

    def action_reclassify_commit(self) -> None:
        """Open modal dialog to change commit type."""
        if self.selection_list.highlighted is None:
            return

        commit_idx = self.selection_list.get_option_at_index(self.selection_list.highlighted).value
        commit = self.commits[commit_idx]

        def _on_reclassify_dismissed(new_type: str | None) -> None:
            if new_type:
                if new_type == "breaking":
                    commit.is_breaking = True
                else:
                    commit.is_breaking = False
                    commit.type = new_type
                self._populate_selections()
                self._refresh_state()

        self.push_screen(ReclassifyModal(), _on_reclassify_dismissed)

    def action_toggle_all(self) -> None:
        """Toggle all visible items in the selection list."""
        current_selected = self.selection_list.selected
        all_options = [opt.value for opt in self.selection_list._options]
        if len(current_selected) == len(all_options):
            self.selection_list.deselect_all()
        else:
            self.selection_list.select_all()

    def action_publish(self) -> None:
        """User approved release."""
        self.confirmed = True
        self.exit()

    def action_quit(self) -> None:
        """User cancelled."""
        self.confirmed = False
        self.exit()
