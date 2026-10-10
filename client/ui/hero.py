"""
Shared left-hand "hero" panel for the Login and Register screens.

Turns the empty background into a professional branded panel with the product
name, a tagline, and the key feature highlights — like a real SaaS sign-in page.
"""
from __future__ import annotations

import customtkinter as ctk

from client.ui import theme

_FEATURES = [
    ("🔒", "Bank-grade security", "AWS IAM controls every single access."),
    ("☁", "Durable cloud storage", "Your files live safely on Amazon S3."),
    ("⟲", "One-click restore", "Bring any file back to any folder, anytime."),
    ("👤", "Private by design", "You only ever see your own backups."),
]


def build_hero(parent) -> ctk.CTkFrame:
    """Create and return the indigo hero panel (caller grids/places it)."""
    hero = ctk.CTkFrame(parent, corner_radius=0, fg_color=theme.PRIMARY)
    hero.grid_columnconfigure(0, weight=1)

    inner = ctk.CTkFrame(hero, fg_color="transparent")
    inner.place(relx=0.5, rely=0.5, anchor="center")

    # Brand
    brand = ctk.CTkFrame(inner, fg_color="transparent")
    brand.pack(anchor="w", pady=(0, 6))
    ctk.CTkLabel(brand, text="☁", font=("Segoe UI", 40),
                 text_color="#FFFFFF").pack(side="left")
    ctk.CTkLabel(brand, text="  CloudVault", font=("Segoe UI Semibold", 34, "bold"),
                 text_color="#FFFFFF").pack(side="left")

    ctk.CTkLabel(
        inner,
        text="Back up your files to the cloud.\nRestore anywhere, anytime.",
        font=("Segoe UI", 16), text_color="#E0E7FF", justify="left",
    ).pack(anchor="w", pady=(0, 26))

    for icon, title, desc in _FEATURES:
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(anchor="w", fill="x", pady=7)
        ctk.CTkLabel(row, text=icon, font=("Segoe UI", 22),
                     text_color="#FFFFFF", width=36).pack(side="left", padx=(0, 10))
        txt = ctk.CTkFrame(row, fg_color="transparent")
        txt.pack(side="left", anchor="w")
        ctk.CTkLabel(txt, text=title, font=("Segoe UI Semibold", 14, "bold"),
                     text_color="#FFFFFF", anchor="w").pack(anchor="w")
        ctk.CTkLabel(txt, text=desc, font=theme.FONT_SMALL,
                     text_color="#C7D2FE", anchor="w").pack(anchor="w")

    ctk.CTkLabel(inner, text="Powered by Amazon Web Services  ·  S3 · IAM",
                 font=theme.FONT_SMALL, text_color="#C7D2FE").pack(
        anchor="w", pady=(28, 0))
    return hero
