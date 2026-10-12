"""Theme layer (spec §4): one engine, N skins.

A theme is a lexicon mapping every agent-visible string. The engine speaks
abstract ids; ThemedView translates tool arguments in (slug -> engine id)
and results out (engine id -> slug/name). Tool names and result keys are
identical across themes — expressiveness lives in content strings only.
"""

from .theme import Theme, ItemLexicon, load_theme, available_themes
from .view import ThemedView

__all__ = ["Theme", "ItemLexicon", "load_theme", "available_themes", "ThemedView"]
