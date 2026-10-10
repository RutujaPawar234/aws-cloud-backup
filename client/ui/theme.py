"""Shared colors and fonts so every screen looks consistent and professional."""

# ---- Brand palette (modern indigo / slate, cloud theme) ----
PRIMARY = "#4F46E5"          # indigo
PRIMARY_HOVER = "#4338CA"
ACCENT = "#06B6D4"           # cyan accent
SUCCESS = "#16A34A"
SUCCESS_HOVER = "#15803D"
WARNING = "#D97706"
DANGER = "#DC2626"
DANGER_HOVER = "#B91C1C"

# Surfaces (tuples = (light, dark) for CustomTkinter)
SIDEBAR = ("#4F46E5", "#111827")     # indigo in light, near-black in dark
SIDEBAR_HOVER = ("#4338CA", "#1F2937")
CARD = ("#FFFFFF", "#1E293B")
CARD_BORDER = ("#E2E8F0", "#334155")
APP_BG = ("#F1F5F9", "#0F172A")
ROW_ALT = ("#F8FAFC", "#243244")
MUTED = ("#64748B", "#94A3B8")
ON_SIDEBAR = "#FFFFFF"
ON_SIDEBAR_MUTED = ("#E0E7FF", "#94A3B8")

# Per-stat-card accents (bar color, soft fill)
STAT_ACCENTS = [
    ("#4F46E5", ("#EEF2FF", "#1E1B4B")),   # files  - indigo
    ("#06B6D4", ("#ECFEFF", "#083344")),   # storage- cyan
    ("#16A34A", ("#F0FDF4", "#052E16")),   # status - green
]

# ---- Fonts (family, size, weight) ----
FONT_BRAND = ("Segoe UI Semibold", 20, "bold")
FONT_TITLE = ("Segoe UI", 26, "bold")
FONT_HEADING = ("Segoe UI", 18, "bold")
FONT_SUBHEADING = ("Segoe UI", 14, "bold")
FONT_BODY = ("Segoe UI", 13)
FONT_SMALL = ("Segoe UI", 11)
FONT_STAT = ("Segoe UI", 32, "bold")
FONT_BADGE = ("Segoe UI Semibold", 11, "bold")
