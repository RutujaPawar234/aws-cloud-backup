"""Small reusable UI widgets."""
from __future__ import annotations

import customtkinter as ctk

from client.ui import theme


def field_label(parent, text: str):
    """A small bold caption placed above an input field."""
    return ctk.CTkLabel(parent, text=text, font=theme.FONT_SUBHEADING,
                        text_color=theme.MUTED, anchor="w")
