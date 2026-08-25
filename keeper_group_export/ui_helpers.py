"""Small presentation helpers and keyboard-shortcut guards."""

from .common import C_DANGER, C_INFO, C_MUTED, C_SUCCESS, C_WARNING


class UIHelpersMixin:
    def _set_status(self, text, *, tone="muted"):
        """Update the footer and vault status indicator consistently."""
        self.footer_status.config(text=text)

        colours = {
            "muted": C_MUTED,
            "success": C_SUCCESS,
            "warning": C_WARNING,
            "danger": C_DANGER,
            "info": C_INFO,
        }
        colour = colours.get(tone, C_MUTED)

        if hasattr(self, "status_dot"):
            self.status_dot.itemconfigure("dot", fill=colour, outline=colour)

    def _focus_search(self):
        """Move keyboard focus to the preview filter."""
        if hasattr(self, "search_entry"):
            self.search_entry.focus_set()
            self.search_entry.select_range(0, "end")

    def _shortcut_export(self):
        """Execute export only when the export control is currently available."""
        if str(self.export_btn["state"]) != "disabled":
            self.export_selected()

    def _shortcut_refresh(self):
        """Refresh the connected vault only when a session exists."""
        if self.params:
            self.refresh_vault()
