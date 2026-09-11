"""Main Textual application for interactive release curation."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Label, SelectionList
from textual.widgets.selection_list import Selection

from releasecraft.changelog.builder import ChangelogBuilder
from releasecraft.models import BumpType, ParsedCommit, SemVerInfo
from releasecraft.parser.semver_calculator import SemVerCalculator
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
                yield Label("Commit Curator (Space: toggle | p: publish)", classes="pane-title")
                selections = []
                for idx, c in enumerate(self.commits):
                    prompt = f"[{c.raw.short_hash}] {c.type.upper()}: {c.subject}"
                    selections.append(Selection(prompt, idx, initial_state=c.included_in_release))

                self.selection_list = SelectionList[int](*selections, id="commit-selector")
                yield self.selection_list

            with Vertical(id="right-pane"):
                self.preview_pane = ChangelogPreviewPane(
                    self.current_markdown,
                    id="changelog-preview",
                )
                yield self.preview_pane

        yield Footer()

    def on_selection_list_selected_changed(self, event: SelectionList.SelectedChanged) -> None:
        """Handle toggle of commits in the list."""
        selected_set = set(event.selection_list.selected)

        for idx, commit in enumerate(self.commits):
            commit.included_in_release = idx in selected_set

        # Recalculate version
        self.next_version, self.bump_type = SemVerCalculator.calculate_next_version(
            current_version=self.current_version,
            commits=self.commits,
        )

        # Update markdown
        new_md, _ = self.builder.build_markdown(
            version=self.next_version,
            commits=self.commits,
            prev_version=self.current_version,
        )
        self.current_markdown = new_md

        # Refresh preview and header
        self.preview_pane.update_content(new_md)
        self.header_widget.current_version = self.current_version
        self.header_widget.next_version = self.next_version
        self.header_widget.bump_type = self.bump_type
        self.header_widget.refresh()

    def action_toggle_all(self) -> None:
        """Toggle all items in the selection list."""
        current_selected = self.selection_list.selected
        if len(current_selected) == len(self.commits):
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
