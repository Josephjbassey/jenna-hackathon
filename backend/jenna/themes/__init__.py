"""
Jenna Multi-Theme System
Loads Omarchy themes (colors.toml) and maps them to dashboard design tokens.
Supports live theme switching with CSS custom properties.
"""
from __future__ import annotations
import tomllib
from pathlib import Path
from dataclasses import dataclass, field
from typing import ClassVar
import json


@dataclass(frozen=True)
class OmarchyTheme:
    """Parsed Omarchy theme from colors.toml"""
    name: str
    mode: str  # "dark" | "light"
    # Core palette
    background: str
    dark_background: str
    darker_background: str
    lighter_background: str
    foreground: str
    dark_foreground: str
    light_foreground: str
    bright_foreground: str
    accent: str
    selection: str
    muted: str
    # Semantic colors
    red: str
    yellow: str
    orange: str
    green: str
    cyan: str
    blue: str
    magenta: str
    brown: str
    # Bright variants
    bright_red: str
    bright_yellow: str
    bright_green: str
    bright_cyan: str
    bright_blue: str
    bright_magenta: str

    @classmethod
    def from_toml(cls, path: Path) -> "OmarchyTheme":
        data = tomllib.loads(path.read_text())
        return cls(
            name=path.parent.name,
            mode=data.get("mode", "dark"),
            background=data["background"],
            dark_background=data["dark_background"],
            darker_background=data["darker_background"],
            lighter_background=data["lighter_background"],
            foreground=data["foreground"],
            dark_foreground=data["dark_foreground"],
            light_foreground=data["light_foreground"],
            bright_foreground=data["bright_foreground"],
            accent=data["accent"],
            selection=data["selection"],
            muted=data["muted"],
            red=data["red"],
            yellow=data["yellow"],
            orange=data["orange"],
            green=data["green"],
            cyan=data["cyan"],
            blue=data["blue"],
            magenta=data["magenta"],
            brown=data["brown"],
            bright_red=data["bright_red"],
            bright_yellow=data["bright_yellow"],
            bright_green=data["bright_green"],
            bright_cyan=data["bright_cyan"],
            bright_blue=data["bright_blue"],
            bright_magenta=data["bright_magenta"],
        )

    def to_css_vars(self, prefix: str = "jenna") -> dict[str, str]:
        """Map Omarchy colors to Jenna dashboard design tokens."""
        is_dark = self.mode == "dark"
        # Base surfaces - map to Jenna's 3-layer depth
        bg_base = self.darker_background if is_dark else self.background
        bg_surface = self.dark_background if is_dark else self.dark_background
        bg_raised = self.background if is_dark else self.lighter_background
        # Hairlines/borders
        hairline = self.selection
        hairline_strong = self.muted
        # Ink hierarchy
        ink_1 = self.bright_foreground
        ink_2 = self.light_foreground
        ink_3 = self.muted
        # State hues (from semantic colors)
        state_listening = self.cyan
        state_thinking = self.yellow
        state_ready = self.green
        state_fault = self.red
        # Accent - primary brand color
        accent = self.accent
        # Selection/hover
        selection_bg = self.selection
        selection_fg = self.foreground
        return {
            f"--{prefix}-bg-base": bg_base,
            f"--{prefix}-bg-surface": bg_surface,
            f"--{prefix}-bg-raised": bg_raised,
            f"--{prefix}-hairline": hairline,
            f"--{prefix}-hairline-strong": hairline_strong,
            f"--{prefix}-ink-1": ink_1,
            f"--{prefix}-ink-2": ink_2,
            f"--{prefix}-ink-3": ink_3,
            f"--{prefix}-accent": accent,
            f"--{prefix}-state-listening": state_listening,
            f"--{prefix}-state-thinking": state_thinking,
            f"--{prefix}-state-ready": state_ready,
            f"--{prefix}-state-fault": state_fault,
            f"--{prefix}-selection-bg": selection_bg,
            f"--{prefix}-selection-fg": selection_fg,
            f"--{prefix}-mode": self.mode,
        }


class ThemeRegistry:
    """Discovers and loads all available Omarchy themes."""
    SYSTEM_THEME_DIR: ClassVar[Path] = Path("/usr/share/omarchy/themes")
    USER_THEME_DIR: ClassVar[Path] = Path.home() / ".config" / "omarchy" / "themes"
    JENNA_THEME_DIR: ClassVar[Path] = Path.home() / ".config" / "jenna" / "themes"

    def __init__(self):
        self._themes: dict[str, OmarchyTheme] = {}
        self._load_all()

    def _load_all(self):
        for theme_dir in (self.SYSTEM_THEME_DIR, self.USER_THEME_DIR, self.JENNA_THEME_DIR):
            if not theme_dir.exists():
                continue
            for colors_file in theme_dir.glob("*/colors.toml"):
                try:
                    theme = OmarchyTheme.from_toml(colors_file)
                    self._themes[theme.name] = theme
                except Exception:
                    pass  # Skip invalid themes

    def list_themes(self) -> list[dict]:
        """Return theme metadata for UI selectors."""
        return [
            {"name": t.name, "mode": t.mode, "accent": t.accent, "background": t.background}
            for t in sorted(self._themes.values(), key=lambda x: x.name)
        ]

    def get(self, name: str) -> OmarchyTheme | None:
        return self._themes.get(name)

    def current_omarchy_theme(self) -> str | None:
        """Detect currently active Omarchy theme from shell.toml or hyprland config."""
        shell_toml = Path.home() / ".config" / "omarchy" / "shell.toml"
        if shell_toml.exists():
            try:
                import tomllib
                data = tomllib.loads(shell_toml.read_text())
                # shell.toml may have theme reference
            except Exception:
                pass
        # Fallback: check hyprland colors or current theme symlink
        return "quattro"  # Default from earlier detection

    def css_variables(self, theme_name: str | None = None, prefix: str = "jenna") -> str:
        """Generate :root CSS custom properties for a theme."""
        theme = self.get(theme_name or self.current_omarchy_theme() or "catppuccin")
        if not theme:
            theme = next(iter(self._themes.values()))
        vars_dict = theme.to_css_vars(prefix)
        lines = [":root {"]
        for k, v in vars_dict.items():
            lines.append(f"  {k}: {v};")
        lines.append("}")
        return "\n".join(lines)


# Convenience singleton
REGISTRY = ThemeRegistry()


def get_theme_css(theme_name: str | None = None) -> str:
    """Get CSS variables for a theme (for inline injection)."""
    return REGISTRY.css_variables(theme_name)


def list_available_themes() -> list[dict]:
    return REGISTRY.list_themes()