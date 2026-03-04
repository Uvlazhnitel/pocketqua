from backend.app.db import models


def calculate_risk_state(
    *,
    current_total_value_usd: float,
    previous_snapshot: models.PortfolioSnapshot | None,
    strategy: models.Strategy,
) -> tuple[float, float, models.RiskMode, models.RiskMode | None]:
    previous_peak = previous_snapshot.peak_value_usd if previous_snapshot else 0.0
    peak_value_usd = max(previous_peak, current_total_value_usd)

    if peak_value_usd > 0:
        drawdown_pct = max(0.0, (peak_value_usd - current_total_value_usd) / peak_value_usd)
    else:
        drawdown_pct = 0.0

    if drawdown_pct >= strategy.drawdown_defense_pct:
        mode = models.RiskMode.DEFENSE
    elif drawdown_pct >= strategy.drawdown_caution_pct:
        mode = models.RiskMode.CAUTION
    else:
        mode = models.RiskMode.NORMAL

    previous_mode = previous_snapshot.risk_mode if previous_snapshot else None
    return peak_value_usd, drawdown_pct, mode, previous_mode
