def build_action_payload(
    *,
    effect: str,
    estimated_cost_eur: float | None,
    risk_note: str | None,
    calculation: dict,
) -> dict:
    return {
        "effect": effect,
        "estimated_cost_eur": estimated_cost_eur,
        "risk_note": risk_note,
        "calculation": calculation,
    }
