def build_action_payload(
    *,
    effect: str,
    estimated_cost_usd: float | None,
    risk_note: str | None,
    calculation: dict,
) -> dict:
    return {
        "effect": effect,
        "estimated_cost_usd": estimated_cost_usd,
        "risk_note": risk_note,
        "calculation": calculation,
    }
