"""Pack register audit (spec §5): measure the mood instead of assuming it.

Continuous prose always carries some genre valence — the audit makes each
pack's residual register a reported number (and later, an analysis
covariate) rather than a vibe. Run it on every pack before spending on the
runs that will share it.
"""

from __future__ import annotations

import re

from .pack import NarrationPack

_CRISIS = re.compile(
    r"\b(failure|fail(ed|ing)?|crisis|disrupt\w*|freeze|frozen|collaps\w*|"
    r"congest\w*|incident|breach|degrad\w*|anomal\w*|escalat\w*|emergenc\w*|"
    r"critical|unresolved|backlog|exhaust\w*|shortag\w*|volatil\w*|strain\w*|"
    r"menac\w*|obstruct\w*)\b",
    re.IGNORECASE,
)
_WARM = re.compile(
    r"\b(cheer\w*|merri\w*|laugh\w*|festiv\w*|delight\w*|jolly|warm\w*|"
    r"hope\w*|bustl\w*|lively|charm\w*|amus\w*|comic\w*|gossip\w*|celebrat\w*)\b",
    re.IGNORECASE,
)


def register_audit(pack: NarrationPack) -> dict:
    """Per-pack register profile: crisis/warm vocabulary rates, length, and
    internal diversity (novelty of each day's narration vs all prior days —
    a de-dramatized pack can quietly collapse into self-repetition, which
    under-delivers richness in exactly one cell)."""
    from ..analysis.novelty import novelty_series

    days = len(pack.entries)
    crisis_days = sum(1 for e in pack.entries if _CRISIS.search(e.text))
    warm_days = sum(1 for e in pack.entries if _WARM.search(e.text))
    novelty = novelty_series([e.text for e in pack.entries])
    return {
        "theme": pack.theme,
        "schedule_seed": pack.schedule_seed,
        "days": days,
        "crisis_day_rate": crisis_days / days if days else None,
        "warm_day_rate": warm_days / days if days else None,
        "fallback_days": len(pack.fallback_days()),
        "mean_chars": (
            sum(len(e.text) for e in pack.entries) / days if days else None
        ),
        "novelty_mean": (sum(novelty) / len(novelty)) if novelty else None,
        "novelty_min": min(novelty[1:]) if len(novelty) > 1 else None,
    }
