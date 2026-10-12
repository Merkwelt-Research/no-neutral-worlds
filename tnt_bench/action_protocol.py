"""Versioned action allowance; historical runs retain their original surface."""

LEGACY_ACTION_PROTOCOL = "legacy"
DISCLOSED_JOURNAL_PROTOCOL = "disclosed_journal_v1"
DAILY_ACTION_ALLOWANCE = 20
JOURNAL_RESPONSE_ALLOWANCE = 3


def validate_action_protocol(protocol: str) -> None:
    if protocol not in (LEGACY_ACTION_PROTOCOL, DISCLOSED_JOURNAL_PROTOCOL):
        raise ValueError(f"unknown action protocol: {protocol}")


def allowance_text(reflection_noun: str) -> str:
    return (
        "You have time for 20 actions per day. Each inspection or attempted "
        "action uses one of these, including an action that cannot be completed. "
        f"Writing your {reflection_noun} does not use up this time; you can "
        "still call end_day after using all 20 actions."
    )
