"""Registration screen."""
from __future__ import annotations

import threading

import customtkinter as ctk

from client.api.client import ApiError
from client.ui import theme
from client.ui.hero import build_hero
from client.ui.widgets import field_label as _field_label
from client.utils.helpers import is_valid_email


class RegisterView(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color=theme.APP_BG)
        self.controller = controller

        # Two-pane layout: hero (left) + form (right)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=5, uniform="auth")
        self.grid_columnconfigure(1, weight=4, uniform="auth")

        build_hero(self).grid(row=0, column=0, sticky="nsew")

        form_area = ctk.CTkFrame(self, fg_color="transparent")
        form_area.grid(row=0, column=1, sticky="nsew")

        card = ctk.CTkFrame(form_area, width=410, corner_radius=20, fg_color=theme.CARD,
                            border_width=1, border_color=theme.CARD_BORDER)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="Create your account", font=theme.FONT_TITLE).grid(
            row=1, column=0, padx=40, pady=(28, 16)
        )

        _field_label(card, "Full Name").grid(row=2, column=0, sticky="w", padx=42)
        self.full_name = ctk.CTkEntry(card, placeholder_text="e.g. Rutuja Pawar",
                                      width=330, height=42, corner_radius=10)
        self.full_name.grid(row=3, column=0, padx=40, pady=(2, 8))

        _field_label(card, "Email").grid(row=4, column=0, sticky="w", padx=42)
        self.email = ctk.CTkEntry(card, placeholder_text="you@example.com", width=330,
                                   height=42, corner_radius=10)
        self.email.grid(row=5, column=0, padx=40, pady=(2, 8))

        _field_label(card, "Password (min 6 chars)").grid(
            row=6, column=0, sticky="w", padx=42)
        pwrow = ctk.CTkFrame(card, fg_color="transparent")
        pwrow.grid(row=7, column=0, padx=40, pady=(2, 8))
        self.password = ctk.CTkEntry(pwrow, placeholder_text="Create a password",
                                     show="•", width=258, height=42, corner_radius=10)
        self.password.pack(side="left")
        self._show_pw = False
        self.show_btn = ctk.CTkButton(
            pwrow, text="Show", width=64, height=42, corner_radius=10,
            fg_color=theme.CARD_BORDER, text_color=theme.PRIMARY,
            hover_color=theme.MUTED, font=theme.FONT_SMALL, command=self._toggle_pw,
        )
        self.show_btn.pack(side="left", padx=(8, 0))

        _field_label(card, "Confirm Password").grid(
            row=8, column=0, sticky="w", padx=42)
        self.confirm = ctk.CTkEntry(card, placeholder_text="Re-enter your password",
                                    show="•", width=330, height=42, corner_radius=10)
        self.confirm.grid(row=9, column=0, padx=40, pady=(2, 8))
        self.confirm.bind("<Return>", lambda _e: self._submit())

        self.status = ctk.CTkLabel(card, text="", font=theme.FONT_SMALL,
                                   text_color=theme.DANGER)
        self.status.grid(row=10, column=0, pady=(4, 0))

        self.reg_btn = ctk.CTkButton(
            card, text="Create Account", width=330, height=44, corner_radius=10,
            font=theme.FONT_SUBHEADING, fg_color=theme.SUCCESS,
            hover_color=theme.SUCCESS_HOVER, command=self._submit,
        )
        self.reg_btn.grid(row=11, column=0, padx=40, pady=(14, 8))

        ctk.CTkButton(
            card, text="Back to Login", width=330, height=42, corner_radius=10,
            fg_color="transparent", border_width=1, border_color=theme.PRIMARY,
            text_color=theme.PRIMARY, hover_color=theme.CARD_BORDER,
            command=controller.show_login,
        ).grid(row=12, column=0, padx=40, pady=(0, 24))

    def _toggle_pw(self) -> None:
        self._show_pw = not self._show_pw
        show = "" if self._show_pw else "•"
        self.password.configure(show=show)
        self.confirm.configure(show=show)
        self.show_btn.configure(text="Hide" if self._show_pw else "Show")

    def reset(self) -> None:
        for e in (self.full_name, self.email, self.password, self.confirm):
            e.delete(0, "end")
        self.status.configure(text="")

    def _set_status(self, text: str, ok: bool = False) -> None:
        self.status.configure(text=text, text_color=theme.SUCCESS if ok else theme.DANGER)

    def _submit(self) -> None:
        name = self.full_name.get().strip()
        email = self.email.get().strip()
        pw = self.password.get()
        confirm = self.confirm.get()

        if not name or not email or not pw or not confirm:
            self._set_status("All fields are required.")
            return
        if not is_valid_email(email):
            self._set_status("Please enter a valid email address.")
            return
        if len(pw) < 6:
            self._set_status("Password must be at least 6 characters.")
            return
        if pw != confirm:
            self._set_status("Passwords do not match.")
            return

        self.reg_btn.configure(state="disabled", text="Creating...")
        self._set_status("")

        def work():
            try:
                self.controller.api.register(name, email, pw)
                self.after(0, self.controller.show_dashboard)
            except ApiError as exc:
                msg = exc.message
                self.after(0, lambda: self._set_status(msg))
            finally:
                self.after(0, lambda: self.reg_btn.configure(
                    state="normal", text="Create Account"))

        threading.Thread(target=work, daemon=True).start()
