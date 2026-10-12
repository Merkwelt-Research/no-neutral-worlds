"""Theme loading and validation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from ..engine import effects
from ..io_utils import read_text
from ..engine.config import EngineConfig

DATA_DIR = Path(__file__).parent / "data"


@dataclass(frozen=True)
class ItemLexicon:
    slug: str  # agent-facing identifier used in tool calls/results
    name: str  # display name used in prose (disclosures, ledger notes)
    desc: str


@dataclass(frozen=True)
class Theme:
    name: str
    meta: dict  # shop_name, shop_noun, persona, currency, supplier, daily_fee_label, world
    items: dict[str, ItemLexicon]  # engine item id -> lexicon
    categories: dict[str, str]  # engine category letter -> themed name
    static_events: dict[str, str]  # effect_type -> terse R- narration line
    system_prompt_template: str  # raw text with {horizon} placeholder
    gm_style: str  # register instructions for R+ pack generation

    def slug_to_id(self, slug: str) -> str | None:
        for item_id, lex in self.items.items():
            if lex.slug == slug:
                return item_id
        return None

    def id_to_slug(self, item_id: str) -> str:
        return self.items[item_id].slug

    def item_name(self, item_id: str) -> str:
        return self.items[item_id].name

    def render_system_prompt(
        self, horizon: int, disclosed: bool = True,
        variants: frozenset | set = frozenset(),
        carrying_rate: str | None = None,
    ) -> str:
        """Render the system prompt. Prompt files may carry conditional
        blocks (`<!--if:tag-->…<!--endif-->`); a block survives iff its tag
        is active. 'disclosed'/'undisclosed' come from the horizon flag;
        further tags (e.g. 'carrying' for the carrying-cost economy) come
        from `variants`. Requesting a variant the template has no block for
        is an error — an undisclosed mechanic is a parity violation. The
        'carrying' block states its rate via {carrying_rate} (economy-
        dependent phrase: DOCTRINE_ECONOMY's 3.0 vs the attenuation arm's
        0.5) — required exactly when 'carrying' is active."""
        active = {"disclosed" if disclosed else "undisclosed", *variants}
        # Strict tags carry a real mechanic: silently dropping them would be
        # a parity violation. Lenient tags (e.g. 'free_storage') disclose the
        # absence of a mechanic; themes that never mention storage may omit
        # them (the main run's themes stay untouched).
        for tag in variants & _STRICT_TAGS:
            if f"<!--if:{tag}-->" not in self.system_prompt_template:
                raise ValueError(
                    f"theme {self.name}: prompt has no '{tag}' variant block — "
                    "the active mechanic would be undisclosed"
                )
        text = _select_variants(self.system_prompt_template, active)
        text = text.replace("{horizon}", str(horizon)) if disclosed else text
        if "{horizon}" in text:
            raise ValueError(
                f"theme {self.name}: undisclosed prompt variant still references horizon"
            )
        if "carrying" in variants:
            if not carrying_rate:
                raise ValueError(
                    f"theme {self.name}: 'carrying' variant requires a "
                    "carrying_rate phrase — an unstated rate is a parity violation"
                )
            text = text.replace("{carrying_rate}", carrying_rate)
        if "{carrying_rate}" in text:
            raise ValueError(
                f"theme {self.name}: rendered prompt still references carrying_rate"
            )
        return text

    @property
    def discloses_storage(self) -> bool:
        """True for themes whose prompt states a storage rule (both the
        carrying rate and the free-storage counterpart). Drives symmetric
        briefing/check_shop disclosure in both economies."""
        return "<!--if:carrying-->" in self.system_prompt_template

    def theme_text(self, text: str) -> str:
        """Translate a canonical engine string (disclosure, ledger note) into
        this theme's vocabulary. Pure substitution — structure is preserved,
        which is what keeps information parity checkable."""
        for item_id, lex in self.items.items():
            text = text.replace(item_id, lex.name)
        for letter, name in self.categories.items():
            if name != letter:
                text = text.replace(f"category {letter}", f"category {name}")
        return text.replace("funds", self.meta["currency"])


_VARIANT_BLOCK = re.compile(
    r"<!--if:([a-z_]+)-->\n?(.*?)<!--endif-->\n?", re.DOTALL
)

# Variant tags whose absence from a template is an error when requested: each
# carries a real mechanic or normative treatment, so silently dropping it
# would be a parity/disclosure violation.
_STRICT_TAGS = frozenset({
    "carrying",
    "exploit",
    "exploit_corrected",
    "prohibition",
    "whatever_it_takes",
    "supplier_email",
    "climate_baseline",
    "climate_integrity",
    "climate_audit",
})


def _select_variants(template: str, active: set) -> str:
    """Keep conditional blocks whose tag is in `active` (markers stripped),
    drop the rest. Text outside any block is shared by all variants."""

    def replace(match: re.Match) -> str:
        return match.group(2) if match.group(1) in active else ""

    return _VARIANT_BLOCK.sub(replace, template)


def available_themes() -> list[str]:
    return sorted(p.stem for p in DATA_DIR.glob("*.yml"))


def load_theme(name: str) -> Theme:
    path = DATA_DIR / f"{name}.yml"
    if not path.exists():
        raise FileNotFoundError(f"no such theme: {name} (have: {available_themes()})")
    data = yaml.safe_load(read_text(path))

    prompt_path = DATA_DIR / data["system_prompt"]
    theme = Theme(
        name=data["name"],
        meta=data["meta"],
        items={
            item_id: ItemLexicon(**lex) for item_id, lex in data["items"].items()
        },
        categories=data["categories"],
        static_events=data["static_events"],
        system_prompt_template=read_text(prompt_path),
        gm_style=data["gm_style"],
    )
    validate_theme(theme)
    return theme


def validate_theme(theme: Theme, config: EngineConfig | None = None) -> None:
    config = config or EngineConfig()

    good_ids = {g.id for g in config.goods}
    if set(theme.items) != good_ids:
        raise ValueError(f"theme {theme.name}: items must cover exactly {sorted(good_ids)}")

    slugs = [lex.slug for lex in theme.items.values()]
    if len(slugs) != len(set(slugs)):
        raise ValueError(f"theme {theme.name}: duplicate item slugs")
    if set(slugs) & good_ids:
        raise ValueError(f"theme {theme.name}: slugs must not collide with engine ids")

    categories = {g.category for g in config.goods}
    if set(theme.categories) != categories:
        raise ValueError(f"theme {theme.name}: categories must cover exactly {sorted(categories)}")

    missing = effects.ALL_EFFECT_TYPES - set(theme.static_events)
    if missing:
        raise ValueError(f"theme {theme.name}: static_events missing {sorted(missing)}")

    required_meta = {
        "shop_name",
        "shop_noun",
        "persona",
        "currency",
        "supplier",
        "daily_fee_label",
        "reflection_noun",
        "world",
    }
    missing = required_meta - set(theme.meta)
    if missing:
        raise ValueError(f"theme {theme.name}: meta missing {sorted(missing)}")
