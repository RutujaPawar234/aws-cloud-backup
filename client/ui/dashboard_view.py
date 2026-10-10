"""
Main dashboard: a sidebar + a swappable content area.

Pages: Home (stats + recent), Backup File, Backup History, About.
All network calls run on a background thread so the UI never freezes.
"""
from __future__ import annotations

import os
import threading
import webbrowser
from tkinter import filedialog, messagebox

import customtkinter as ctk

from client.api.client import ApiError
from client.ui import theme
from client.utils.helpers import format_date, format_size


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.api = controller.api

        self._files_cache: list[dict] = []
        self._selected_backup_path: str | None = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=24, pady=20)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    # ----------------------------------------------------------------- setup
    def on_show(self) -> None:
        """Called every time the dashboard becomes visible after login."""
        user = self.api.user or {}
        self.welcome.configure(text=f"Welcome, {user.get('full_name', 'User')}")
        self.show_home()

    def _build_sidebar(self) -> None:
        bar = ctk.CTkFrame(self, width=232, corner_radius=0, fg_color=theme.SIDEBAR)
        bar.grid(row=0, column=0, sticky="nsew")
        bar.grid_propagate(False)

        # Brand
        brand = ctk.CTkFrame(bar, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(24, 2))
        ctk.CTkLabel(brand, text="☁", font=("Segoe UI", 26),
                     text_color=theme.ON_SIDEBAR).pack(side="left")
        ctk.CTkLabel(brand, text="  CloudVault", font=theme.FONT_BRAND,
                     text_color=theme.ON_SIDEBAR).pack(side="left")
        ctk.CTkLabel(bar, text="AWS Backup & Restore", font=theme.FONT_SMALL,
                     text_color=theme.ON_SIDEBAR_MUTED).pack(padx=22, anchor="w")

        # Divider
        ctk.CTkFrame(bar, height=1, fg_color=theme.ON_SIDEBAR_MUTED).pack(
            fill="x", padx=18, pady=(16, 4))

        self.welcome = ctk.CTkLabel(bar, text="Welcome", font=theme.FONT_SUBHEADING,
                                    text_color=theme.ON_SIDEBAR)
        self.welcome.pack(padx=22, pady=(10, 18), anchor="w")

        nav = [
            ("🏠   Dashboard", self.show_home),
            ("➕   Backup File", self.show_backup),
            ("🗂   Backup History", self.show_history),
            ("ℹ    About", self.show_about),
        ]
        self._nav_buttons = []
        for text, cmd in nav:
            btn = ctk.CTkButton(
                bar, text=text, anchor="w", height=44, corner_radius=10,
                fg_color="transparent", hover_color=theme.SIDEBAR_HOVER,
                text_color=theme.ON_SIDEBAR, font=theme.FONT_BODY,
                command=lambda c=cmd, t=text: self._nav_to(c, t),
            )
            btn.pack(fill="x", padx=14, pady=3)
            self._nav_buttons.append((btn, text))

        # Bottom controls
        ctk.CTkButton(
            bar, text="⎋   Logout", anchor="w", height=44, corner_radius=10,
            fg_color="transparent", hover_color=theme.DANGER,
            text_color=theme.ON_SIDEBAR, font=theme.FONT_BODY,
            command=self._logout,
        ).pack(fill="x", padx=14, pady=(3, 14), side="bottom")

        self._appearance = ctk.CTkSegmentedButton(
            bar, values=["Dark", "Light"], command=self._set_appearance,
            fg_color=theme.SIDEBAR_HOVER, selected_color=theme.ACCENT,
            selected_hover_color=theme.ACCENT, unselected_color=theme.SIDEBAR_HOVER,
            text_color=theme.ON_SIDEBAR,
        )
        self._appearance.set("Light")
        self._appearance.pack(fill="x", padx=16, pady=(3, 6), side="bottom")
        ctk.CTkLabel(bar, text="Appearance", font=theme.FONT_SMALL,
                     text_color=theme.ON_SIDEBAR_MUTED).pack(
            padx=22, anchor="w", side="bottom")

    def _nav_to(self, cmd, text: str) -> None:
        """Highlight the active nav item and switch page."""
        for btn, t in getattr(self, "_nav_buttons", []):
            btn.configure(fg_color=(theme.SIDEBAR_HOVER if t == text else "transparent"))
        cmd()

    def _set_appearance(self, mode: str) -> None:
        ctk.set_appearance_mode(mode.lower())

    def _clear_content(self) -> None:
        for w in self.content.winfo_children():
            w.destroy()

    def _logout(self) -> None:
        self.api.logout()
        self.controller.show_login()

    def _open_console(self) -> None:
        """Open the AWS S3 console in the browser (handy during the demo)."""
        webbrowser.open("https://s3.console.aws.amazon.com/s3/buckets")

    # ------------------------------------------------------------ HOME page
    def show_home(self) -> None:
        self._clear_content()
        wrap = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        wrap.grid(row=0, column=0, sticky="nsew")
        wrap.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(wrap, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Dashboard", font=theme.FONT_TITLE).grid(
            row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="⟳  Refresh", width=110, height=38,
                      corner_radius=10, command=self.show_home,
                      fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER).grid(
            row=0, column=1, sticky="e")

        # Welcome banner
        name = (self.api.user or {}).get("full_name", "User").split(" ")[0]
        banner = ctk.CTkFrame(wrap, corner_radius=16, fg_color=theme.PRIMARY, height=96)
        banner.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        banner.grid_propagate(False)
        banner.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(banner, text=f"Hi {name} 👋  Welcome to CloudVault",
                     font=("Segoe UI Semibold", 18, "bold"),
                     text_color="#FFFFFF").grid(row=0, column=0, sticky="w",
                                                padx=22, pady=(20, 0))
        ctk.CTkLabel(banner,
                     text="Your files are backed up on Amazon S3 — safe, private and "
                          "ready to restore anytime.",
                     font=theme.FONT_BODY, text_color="#E0E7FF").grid(
            row=1, column=0, sticky="w", padx=22, pady=(2, 0))
        ctk.CTkButton(banner, text="☁  Open S3 Console", width=160, height=36,
                      corner_radius=10, fg_color="#FFFFFF", text_color=theme.PRIMARY,
                      hover_color="#E0E7FF", font=theme.FONT_SUBHEADING,
                      command=self._open_console).grid(
            row=0, column=1, rowspan=2, padx=22)

        # Stat cards
        stats = ctk.CTkFrame(wrap, fg_color="transparent")
        stats.grid(row=2, column=0, sticky="ew", pady=8)
        stats.grid_columnconfigure((0, 1, 2), weight=1, uniform="stat")
        self.card_total = self._stat_card(stats, 0, "Total Files", "0", "🗂", 0,
                                           "files backed up")
        self.card_storage = self._stat_card(stats, 1, "Storage Used", "0 B", "💾", 1,
                                             "on Amazon S3")
        self.card_recent = self._stat_card(stats, 2, "Last Backup", "—", "🕑", 2,
                                            "most recent")

        # Info strip (professional detail row)
        strip = ctk.CTkFrame(wrap, corner_radius=14, fg_color=theme.CARD,
                             border_width=1, border_color=theme.CARD_BORDER)
        strip.grid(row=3, column=0, sticky="ew", pady=(10, 2))
        strip.grid_columnconfigure((0, 1, 2), weight=1, uniform="info")
        self._info_chip(strip, 0, "☁", "Cloud Storage", "Amazon S3")
        self._info_chip(strip, 1, "🛡", "Security", "AWS IAM · JWT")
        self._info_chip(strip, 2, "👤", "Signed in as",
                        (self.api.user or {}).get("email", "—"))

        ctk.CTkButton(
            wrap, text="➕   BACKUP A FILE", height=50, font=theme.FONT_SUBHEADING,
            corner_radius=12, fg_color=theme.SUCCESS, hover_color=theme.SUCCESS_HOVER,
            command=self.show_backup,
        ).grid(row=4, column=0, sticky="ew", pady=16)

        rh = ctk.CTkFrame(wrap, fg_color="transparent")
        rh.grid(row=5, column=0, sticky="ew", pady=(6, 6))
        rh.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(rh, text="Recent Backups", font=theme.FONT_HEADING).grid(
            row=0, column=0, sticky="w")
        ctk.CTkButton(rh, text="View all →", width=90, height=30, corner_radius=8,
                      fg_color="transparent", text_color=theme.PRIMARY,
                      hover_color=theme.CARD_BORDER, font=theme.FONT_SUBHEADING,
                      command=self.show_history).grid(row=0, column=1, sticky="e")
        self.recent_box = ctk.CTkFrame(wrap, corner_radius=14, fg_color=theme.CARD,
                                       border_width=1, border_color=theme.CARD_BORDER)
        self.recent_box.grid(row=6, column=0, sticky="ew")
        self.recent_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.recent_box, text="Loading…", text_color=theme.MUTED).pack(
            pady=20)

        self._load_files(self._render_home_data)

    def _stat_card(self, parent, col, label, value, icon, accent_idx, caption=""):
        accent, _fill = theme.STAT_ACCENTS[accent_idx]
        card = ctk.CTkFrame(parent, corner_radius=14, height=118, fg_color=theme.CARD,
                            border_width=1, border_color=theme.CARD_BORDER)
        card.grid(row=0, column=col, sticky="ew", padx=6)
        card.pack_propagate(False)

        ctk.CTkFrame(card, width=6, corner_radius=3, fg_color=accent).pack(
            side="left", fill="y", padx=(10, 0), pady=16)

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=14, pady=14)

        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=label.upper(), font=theme.FONT_SMALL,
                     text_color=theme.MUTED).pack(side="left")
        ctk.CTkLabel(top, text=icon, font=("Segoe UI", 20)).pack(side="right")

        val = ctk.CTkLabel(body, text=value, font=theme.FONT_STAT, text_color=accent)
        val.pack(anchor="w", pady=(4, 0))
        ctk.CTkLabel(body, text=caption, font=theme.FONT_SMALL,
                     text_color=theme.MUTED).pack(anchor="w")
        return val

    def _info_chip(self, parent, col, icon, label, value):
        chip = ctk.CTkFrame(parent, fg_color="transparent")
        chip.grid(row=0, column=col, sticky="ew", padx=16, pady=14)
        ctk.CTkLabel(chip, text=icon, font=("Segoe UI", 22)).pack(side="left", padx=(0, 10))
        txt = ctk.CTkFrame(chip, fg_color="transparent")
        txt.pack(side="left", anchor="w")
        ctk.CTkLabel(txt, text=label, font=theme.FONT_SMALL,
                     text_color=theme.MUTED, anchor="w").pack(anchor="w")
        ctk.CTkLabel(txt, text=value, font=theme.FONT_SUBHEADING, anchor="w").pack(
            anchor="w")

    def _render_home_data(self, files: list[dict]) -> None:
        if not self.recent_box.winfo_exists():
            return  # user navigated away before the data arrived
        total = len(files)
        total_bytes = sum(int(f.get("file_size", 0)) for f in files)
        self.card_total.configure(text=str(total))
        self.card_storage.configure(text=format_size(total_bytes))
        last = format_date(files[0]["uploaded_at"]) if files else "—"
        self.card_recent.configure(text=last, font=theme.FONT_HEADING)

        for w in self.recent_box.winfo_children():
            w.destroy()

        # header row
        hdr = ctk.CTkFrame(self.recent_box, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
        hdr.grid_columnconfigure(0, weight=1)
        for i, (txt, w) in enumerate(
                [("File Name", 240), ("Size", 90), ("Date", 110), ("", 100)]):
            ctk.CTkLabel(hdr, text=txt, font=theme.FONT_SUBHEADING, width=w,
                         anchor="w").grid(row=0, column=i, sticky="w")

        if not files:
            ctk.CTkLabel(self.recent_box, text="No backups yet. Click BACKUP A FILE to start.",
                         text_color=theme.MUTED).grid(row=1, column=0, pady=18)
            return

        for idx, f in enumerate(files[:5], start=1):
            row = ctk.CTkFrame(self.recent_box, fg_color="transparent")
            row.grid(row=idx, column=0, sticky="ew", padx=14, pady=3)
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(row, text="📄  " + f["file_name"], anchor="w", width=240).grid(
                row=0, column=0, sticky="w")
            ctk.CTkLabel(row, text=format_size(int(f["file_size"])), width=90,
                         anchor="w", text_color=theme.MUTED).grid(row=0, column=1)
            ctk.CTkLabel(row, text=format_date(f["uploaded_at"]), width=110,
                         anchor="w", text_color=theme.MUTED).grid(row=0, column=2)
            ctk.CTkButton(row, text="⬇ Download", width=96, height=28, corner_radius=8,
                          font=theme.FONT_SMALL, fg_color=theme.ACCENT,
                          hover_color=theme.PRIMARY_HOVER,
                          command=lambda ff=f: self._download(ff)).grid(row=0, column=3)
        ctk.CTkLabel(self.recent_box, text="").grid(row=6, column=0, pady=4)

    # ---------------------------------------------------------- BACKUP page
    def show_backup(self) -> None:
        self._clear_content()
        self._selected_backup_path = None
        wrap = ctk.CTkFrame(self.content, fg_color="transparent")
        wrap.grid(row=0, column=0, sticky="nsew")
        wrap.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(wrap, text="Backup File", font=theme.FONT_TITLE).grid(
            row=0, column=0, sticky="w", pady=(0, 16))

        card = ctk.CTkFrame(wrap, corner_radius=14, fg_color=theme.CARD, border_width=1, border_color=theme.CARD_BORDER)
        card.grid(row=1, column=0, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            card, text="📁  Choose a file…", height=46, font=theme.FONT_SUBHEADING,
            fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
            command=self._choose_file,
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(22, 10))

        self.file_info = ctk.CTkLabel(card, text="No file selected.",
                                      font=theme.FONT_BODY, text_color=theme.MUTED,
                                      justify="left")
        self.file_info.grid(row=1, column=0, sticky="w", padx=20, pady=6)

        self.backup_progress = ctk.CTkProgressBar(card)
        self.backup_progress.set(0)
        self.backup_progress.grid(row=2, column=0, sticky="ew", padx=20, pady=(6, 2))
        self.backup_progress.grid_remove()

        self.backup_status = ctk.CTkLabel(card, text="", font=theme.FONT_BODY)
        self.backup_status.grid(row=3, column=0, sticky="w", padx=20, pady=4)

        self.confirm_btn = ctk.CTkButton(
            card, text="✓  Confirm Backup", height=46, font=theme.FONT_SUBHEADING,
            fg_color=theme.SUCCESS, hover_color=theme.SUCCESS_HOVER,
            state="disabled", command=self._confirm_backup,
        )
        self.confirm_btn.grid(row=4, column=0, sticky="ew", padx=20, pady=(10, 22))

    def _choose_file(self) -> None:
        path = filedialog.askopenfilename(title="Select a file to back up")
        if not path:
            return
        self._selected_backup_path = path
        size = os.path.getsize(path)
        name = os.path.basename(path)
        ext = name.rsplit(".", 1)[-1].upper() if "." in name else "FILE"
        self.file_info.configure(
            text=f"File:  {name}\nSize:  {format_size(size)}\nType:  {ext}",
            text_color=("black", "white"),
        )
        self.backup_status.configure(text="")
        self.confirm_btn.configure(state="normal")

    def _confirm_backup(self) -> None:
        path = self._selected_backup_path
        if not path:
            return
        self.confirm_btn.configure(state="disabled", text="Uploading…")
        self.backup_progress.grid()
        self.backup_progress.configure(mode="indeterminate")
        self.backup_progress.start()
        self.backup_status.configure(text="Uploading to cloud…", text_color=theme.MUTED)

        def work():
            try:
                self.api.upload(path)
                self.after(0, lambda: self._backup_done(True, "Backup completed successfully!"))
            except ApiError as exc:
                msg = exc.message
                self.after(0, lambda: self._backup_done(False, msg))
            except OSError:
                self.after(0, lambda: self._backup_done(
                    False, "Could not read the selected file."))

        threading.Thread(target=work, daemon=True).start()

    def _backup_done(self, ok: bool, msg: str) -> None:
        self.backup_progress.stop()
        self.backup_progress.grid_remove()
        self.confirm_btn.configure(state="normal", text="✓  Confirm Backup")
        self.backup_status.configure(
            text=("✓ " if ok else "✗ ") + msg,
            text_color=theme.SUCCESS if ok else theme.DANGER,
        )
        if ok:
            self._selected_backup_path = None
            self.confirm_btn.configure(state="disabled")

    # --------------------------------------------------------- HISTORY page
    def show_history(self) -> None:
        self._clear_content()
        wrap = ctk.CTkFrame(self.content, fg_color="transparent")
        wrap.grid(row=0, column=0, sticky="nsew")
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(wrap, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top, text="Backup History", font=theme.FONT_TITLE).grid(
            row=0, column=0, sticky="w")
        ctk.CTkButton(top, text="⟳  Refresh", width=110, command=self.show_history,
                      fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER).grid(
            row=0, column=1, padx=(8, 0))

        self.search = ctk.CTkEntry(wrap, placeholder_text="🔍  Search by file name…",
                                   height=40)
        self.search.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.search.bind("<KeyRelease>", lambda _e: self._render_history())

        self.hist_box = ctk.CTkScrollableFrame(wrap, corner_radius=12)
        self.hist_box.grid(row=2, column=0, sticky="nsew")
        self.hist_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.hist_box, text="Loading…", text_color=theme.MUTED).pack(pady=20)

        self._load_files(lambda files: self._render_history())

    def _render_history(self) -> None:
        if not self.hist_box.winfo_exists():
            return  # user navigated away before the data arrived
        for w in self.hist_box.winfo_children():
            w.destroy()

        query = (self.search.get() or "").strip().lower()
        files = [f for f in self._files_cache
                 if query in f["file_name"].lower()] if query else self._files_cache

        # header
        hdr = ctk.CTkFrame(self.hist_box, fg_color=theme.PRIMARY, corner_radius=8)
        hdr.pack(fill="x", padx=6, pady=(6, 6))
        cols = [("FILE NAME", 180), ("SIZE", 70), ("TYPE", 55),
                ("DATE", 100), ("STATUS", 95), ("ACTIONS", 240)]
        for txt, w in cols:
            ctk.CTkLabel(hdr, text=txt, font=theme.FONT_BADGE, width=w,
                         anchor="w", text_color="#FFFFFF").pack(
                side="left", padx=4, pady=9)

        if not files:
            ctk.CTkLabel(self.hist_box, text="No backups found.",
                         text_color=theme.MUTED).pack(pady=24)
            return

        for i, f in enumerate(files):
            self._history_row(f, i)

    def _history_row(self, f: dict, idx: int) -> None:
        bg = theme.ROW_ALT if idx % 2 else theme.CARD
        row = ctk.CTkFrame(self.hist_box, fg_color=bg, corner_radius=8)
        row.pack(fill="x", padx=6, pady=2)
        ctk.CTkLabel(row, text=f["file_name"], width=180, anchor="w",
                     font=theme.FONT_BODY).pack(side="left", padx=4, pady=6)
        ctk.CTkLabel(row, text=format_size(int(f["file_size"])), width=70, anchor="w",
                     text_color=theme.MUTED).pack(side="left", padx=4)
        ctk.CTkLabel(row, text=f.get("file_type", "-"), width=55, anchor="w",
                     text_color=theme.MUTED).pack(side="left", padx=4)
        ctk.CTkLabel(row, text=format_date(f["uploaded_at"]), width=100, anchor="w",
                     text_color=theme.MUTED).pack(side="left", padx=4)

        # status badge (pill)
        badge_wrap = ctk.CTkFrame(row, fg_color="transparent", width=95)
        badge_wrap.pack(side="left", padx=4)
        pill = ctk.CTkFrame(badge_wrap, fg_color=theme.STAT_ACCENTS[2][1],
                            corner_radius=10)
        pill.pack(anchor="w")
        ctk.CTkLabel(pill, text="● " + f.get("status", "Backed Up"),
                     font=theme.FONT_BADGE, text_color=theme.SUCCESS).pack(
            padx=10, pady=3)

        actions = ctk.CTkFrame(row, fg_color="transparent", width=240)
        actions.pack(side="left", padx=4)
        ctk.CTkButton(actions, text="⬇ Download", width=76, height=30, corner_radius=8,
                      font=theme.FONT_SMALL, fg_color=theme.ACCENT,
                      hover_color=theme.PRIMARY_HOVER,
                      command=lambda: self._download(f)).pack(side="left", padx=2)
        ctk.CTkButton(actions, text="⟲ Restore", width=74, height=30, corner_radius=8,
                      font=theme.FONT_SMALL, fg_color=theme.PRIMARY,
                      hover_color=theme.PRIMARY_HOVER,
                      command=lambda: self._restore(f)).pack(side="left", padx=2)
        ctk.CTkButton(actions, text="🗑", width=36, height=30, corner_radius=8,
                      font=theme.FONT_SMALL, fg_color=theme.DANGER,
                      hover_color=theme.DANGER_HOVER,
                      command=lambda: self._delete(f)).pack(side="left", padx=2)

    # --------------------------------------------------- download / restore
    @staticmethod
    def _default_download_dir() -> str:
        d = os.path.join(os.path.expanduser("~"), "Downloads")
        return d if os.path.isdir(d) else os.path.expanduser("~")

    @staticmethod
    def _unique_path(folder: str, name: str) -> str:
        """Return a path in folder that does not overwrite an existing file."""
        path = os.path.join(folder, name)
        if not os.path.exists(path):
            return path
        base, ext = os.path.splitext(name)
        i = 1
        while os.path.exists(os.path.join(folder, f"{base} ({i}){ext}")):
            i += 1
        return os.path.join(folder, f"{base} ({i}){ext}")

    def _download(self, f: dict) -> None:
        """One-click download straight to the user's Downloads folder."""
        folder = self._default_download_dir()
        save_path = self._unique_path(folder, f["file_name"])
        win = self._busy_window("Downloading…", f"Downloading {f['file_name']}")

        def work():
            try:
                self.api.download(f["file_id"], save_path)
                self.after(0, lambda: (win.destroy(), messagebox.showinfo(
                    "Download complete",
                    f"Saved to:\n{save_path}")))
            except ApiError as exc:
                msg = exc.message
                self.after(0, lambda: (win.destroy(), messagebox.showerror(
                    "Download failed", msg)))
            except OSError:
                self.after(0, lambda: (win.destroy(), messagebox.showerror(
                    "Download failed", "Could not save the file to Downloads.")))

        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------ restore / delete
    def _restore(self, f: dict) -> None:
        folder = filedialog.askdirectory(title="Choose a folder to restore into")
        if not folder:
            return
        save_path = os.path.join(folder, f["file_name"])

        if os.path.exists(save_path):
            if not messagebox.askyesno(
                "File already exists",
                f"'{f['file_name']}' already exists in that folder.\n\n"
                "Do you want to replace it?",
            ):
                return

        win = self._busy_window("Restoring…", f"Downloading {f['file_name']}")

        def work():
            try:
                self.api.download(f["file_id"], save_path)
                self.after(0, lambda: (win.destroy(), messagebox.showinfo(
                    "Restore complete", "File restored successfully!")))
            except ApiError as exc:
                msg = exc.message
                self.after(0, lambda: (win.destroy(), messagebox.showerror(
                    "Restore failed", msg)))
            except OSError:
                self.after(0, lambda: (win.destroy(), messagebox.showerror(
                    "Restore failed", "Could not write the file to that folder.")))

        threading.Thread(target=work, daemon=True).start()

    def _delete(self, f: dict) -> None:
        if not messagebox.askyesno(
            "Delete cloud backup",
            f"Are you sure you want to delete the cloud backup of "
            f"'{f['file_name']}'?\n\nThis will NOT delete any local copy.",
        ):
            return

        win = self._busy_window("Deleting…", "Removing cloud backup")

        def work():
            try:
                self.api.delete(f["file_id"])
                self.after(0, lambda: (win.destroy(), self.show_history()))
            except ApiError as exc:
                msg = exc.message
                self.after(0, lambda: (win.destroy(), messagebox.showerror(
                    "Delete failed", msg)))

        threading.Thread(target=work, daemon=True).start()

    def _busy_window(self, title: str, message: str) -> ctk.CTkToplevel:
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("320x120")
        win.transient(self.winfo_toplevel())
        win.grab_set()
        ctk.CTkLabel(win, text=message, font=theme.FONT_BODY).pack(pady=(24, 10))
        bar = ctk.CTkProgressBar(win, mode="indeterminate", width=240)
        bar.pack(pady=4)
        bar.start()
        return win

    # -------------------------------------------------------------- ABOUT
    def show_about(self) -> None:
        self._clear_content()
        wrap = ctk.CTkFrame(self.content, fg_color="transparent")
        wrap.grid(row=0, column=0, sticky="nsew")
        wrap.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(wrap, text="About", font=theme.FONT_TITLE).grid(
            row=0, column=0, sticky="w", pady=(0, 16))
        card = ctk.CTkFrame(wrap, corner_radius=14, fg_color=theme.CARD, border_width=1, border_color=theme.CARD_BORDER)
        card.grid(row=1, column=0, sticky="ew")
        text = (
            "AWS Cloud-Based File Backup & Restore Application\n\n"
            "A desktop app that backs up your files to the cloud and restores "
            "them on demand.\n\n"
            "• Desktop UI:  Python + CustomTkinter\n"
            "• Backend:  FastAPI (REST API)\n"
            "• Cloud:  Amazon S3 (files) + DynamoDB (metadata)\n"
            "• Security:  AWS IAM\n\n"
            f"Backend URL:  {self.api.base_url}\n\n"
            "Cloud Computing ISE Project."
        )
        ctk.CTkLabel(card, text=text, font=theme.FONT_BODY, justify="left").pack(
            padx=24, pady=24, anchor="w")

    # -------------------------------------------------------- data loading
    def _load_files(self, on_done) -> None:
        """Fetch the user's files on a background thread, then call on_done(files)."""
        def work():
            try:
                files = self.api.list_files()
                self._files_cache = files
                self.after(0, lambda: on_done(files))
            except ApiError as exc:
                msg = exc.message
                self._files_cache = []
                self.after(0, lambda: on_done([]))
                self.after(0, lambda: messagebox.showerror("Error", msg))

        threading.Thread(target=work, daemon=True).start()
