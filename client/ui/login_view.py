"""Login screen."""
from __future__ import annotations

import threading

import customtkinter as ctk

from client.api.client import ApiError
from client.ui import theme
from client.ui.hero import build_hero
from client.ui.widgets import field_label as _field_label


class LoginView(ctk.CTkFrame):
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

        # Center card in the right pane
        card = ctk.CTkFrame(form_area, width=400, corner_radius=20, fg_color=theme.CARD,
                            border_width=1, border_color=theme.CARD_BORDER)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="Welcome back", font=theme.FONT_TITLE).grid(
            row=1, column=0, padx=40, pady=(36, 2))
        ctk.CTkLabel(
            card, text="Sign in to continue to CloudVault", font=theme.FONT_BODY,
            text_color=theme.MUTED,
        ).grid(row=2, column=0, pady=(0, 20))

        # Email
        _field_label(card, "Email").grid(row=3, column=0, sticky="w", padx=42)
        self.email = ctk.CTkEntry(card, placeholder_text="you@example.com", width=330,
                                   height=44, corner_radius=10)
        self.email.grid(row=4, column=0, padx=40, pady=(2, 10))

        # Password (with show/hide)
        _field_label(card, "Password").grid(row=5, column=0, sticky="w", padx=42)
        pwrow = ctk.CTkFrame(card, fg_color="transparent")
        pwrow.grid(row=6, column=0, padx=40, pady=(2, 10))
        self.password = ctk.CTkEntry(pwrow, placeholder_text="Enter your password",
                                     show="•", width=258, height=44, corner_radius=10)
        self.password.pack(side="left")
        self.password.bind("<Return>", lambda _e: self._login())
        self._show_pw = False
        self.show_btn = ctk.CTkButton(
            pwrow, text="Show", width=64, height=44, corner_radius=10,
            fg_color=theme.CARD_BORDER, text_color=theme.PRIMARY,
            hover_color=theme.MUTED, font=theme.FONT_SMALL,
            command=self._toggle_pw,
        )
        self.show_btn.pack(side="left", padx=(8, 0))

        self.status = ctk.CTkLabel(card, text="", font=theme.FONT_SMALL,
                                   text_color=theme.DANGER)
        self.status.grid(row=7, column=0, pady=(2, 0))

        self.login_btn = ctk.CTkButton(
            card, text="Login", width=330, height=44, font=theme.FONT_SUBHEADING,
            corner_radius=10, fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
            command=self._login,
        )
        self.login_btn.grid(row=8, column=0, padx=40, pady=(14, 8))

        ctk.CTkButton(
            card, text="Create Account", width=330, height=42, corner_radius=10,
            fg_color="transparent", border_width=1, border_color=theme.PRIMARY,
            text_color=theme.PRIMARY, hover_color=theme.CARD_BORDER,
            command=controller.show_register,
        ).grid(row=9, column=0, padx=40, pady=(0, 12))

        ctk.CTkLabel(card, text="Secured with AWS S3 + IAM",
                     font=theme.FONT_SMALL, text_color=theme.MUTED).grid(
            row=10, column=0, pady=(0, 26))

    def _toggle_pw(self) -> None:
        self._show_pw = not self._show_pw
        self.password.configure(show="" if self._show_pw else "•")
        self.show_btn.configure(text="Hide" if self._show_pw else "Show")

    # -- actions ------------------------------------------------------------
    def reset(self) -> None:
        self.password.delete(0, "end")
        self.status.configure(text="")

    def _set_status(self, text: str, ok: bool = False) -> None:
        self.status.configure(text=text, text_color=theme.SUCCESS if ok else theme.DANGER)

    def _login(self) -> None:
        email = self.email.get().strip()
        password = self.password.get()
        if not email or not password:
            self._set_status("Please enter email and password.")
            return

        self.login_btn.configure(state="disabled", text="Signing in...")
        self._set_status("")

        def work():
            try:
                self.controller.api.login(email, password)
                self.after(0, self.controller.show_dashboard)
            except ApiError as exc:
                msg = exc.message
                self.after(0, lambda: self._set_status(msg))
            finally:
                self.after(0, lambda: self.login_btn.configure(
                    state="normal", text="Login"))

        threading.Thread(target=work, daemon=True).start()
