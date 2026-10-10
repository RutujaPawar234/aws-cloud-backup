"""
Desktop application entry point.

Run from the project root (cloud-backup-app/):
    python -m client.main
"""
from __future__ import annotations

import customtkinter as ctk

from client.api.client import ApiClient
from client.ui import theme
from client.ui.dashboard_view import DashboardView
from client.ui.login_view import LoginView
from client.ui.register_view import RegisterView
from client.utils.config import get_backend_url

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Guarantee input text is always readable in BOTH light and dark modes
# ([light, dark]). Without this, some CustomTkinter builds render entry text
# too light to see on a light background.
ctk.ThemeManager.theme["CTkEntry"]["text_color"] = ["#111827", "#F8FAFC"]
ctk.ThemeManager.theme["CTkEntry"]["placeholder_text_color"] = ["#64748B", "#94A3B8"]
ctk.ThemeManager.theme["CTkEntry"]["fg_color"] = ["#FFFFFF", "#1E293B"]
ctk.ThemeManager.theme["CTkEntry"]["border_color"] = ["#CBD5E1", "#334155"]


class App(ctk.CTk):
    """Top-level window that swaps between Login, Register and Dashboard."""

    def __init__(self) -> None:
        super().__init__()
        self.title("CloudVault — AWS Backup & Restore")
        self.configure(fg_color=theme.APP_BG)
        self._center(1020, 680)
        self.minsize(880, 600)

        # One shared API client for the whole session.
        self.api = ApiClient(get_backend_url())

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        self.login_view = LoginView(self.container, self)
        self.register_view = RegisterView(self.container, self)
        self.dashboard_view = DashboardView(self.container, self)
        for v in (self.login_view, self.register_view, self.dashboard_view):
            v.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_login()

    def _center(self, w: int, h: int) -> None:
        """Size the window and place it in the middle of the screen."""
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = (sw - w) // 2, max(0, (sh - h) // 2 - 20)
        self.geometry(f"{w}x{h}+{x}+{y}")

    # -- navigation ---------------------------------------------------------
    def show_login(self) -> None:
        self.login_view.reset()
        self.login_view.lift()

    def show_register(self) -> None:
        self.register_view.reset()
        self.register_view.lift()

    def show_dashboard(self) -> None:
        self.dashboard_view.lift()
        self.dashboard_view.on_show()


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
