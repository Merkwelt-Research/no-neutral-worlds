"""Narration layer (spec §5): the R axis.

R- cells use fixed terse lines from the theme lexicon. R+ cells use a
pre-generated narration pack: GM prose generated once per (schedule, theme),
agent-agnostic, leak-guarded at generation time, stored as a YAML artifact.
No run's text ever depends on the agent's trajectory.
"""

from .guards import guard_narration
from .pack import NarrationPack, PackEntry, generate_pack
from .audit import register_audit

__all__ = ["NarrationPack", "PackEntry", "generate_pack", "guard_narration", "register_audit"]
