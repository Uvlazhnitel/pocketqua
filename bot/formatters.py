from __future__ import annotations


def format_actions(actions: list[dict]) -> str:
    if not actions:
        return "PocketQuant Actions (Top 5 New)\nNo new actions."

    lines = ["PocketQuant Actions (Top 5 New)"]
    for action in actions:
        lines.append(f"#{action['id']} [{action['action_type']}] {action['title']}")
        lines.append(f"Reason: {action['reason']}")
    lines.append("Use /explain <id>")
    return "\n".join(lines)


def format_portfolio(summary: dict, risk: dict) -> str:
    lines = [
        "PocketQuant Portfolio",
        f"Total: {summary['total_value_usd']:.2f} USD",
        f"Risk mode: {risk['risk_mode']} (drawdown {risk['drawdown_pct']:.2%})",
    ]
    for row in summary.get("assets", [])[:5]:
        lines.append(f"- {row['symbol']}: {row['value_usd']:.2f} USD ({row['weight']:.2%})")
    warnings = summary.get("warnings", [])
    if warnings:
        lines.append("Warnings:")
        lines.extend(f"- {w}" for w in warnings)
    return "\n".join(lines)


def format_staking(rows: list[dict]) -> str:
    if not rows:
        return "Staking\nNo staking positions."

    lines = ["Staking"]
    for row in rows:
        unlock = row.get("unlock_at") or "n/a"
        claim = row.get("next_claim_at") or "n/a"
        lines.append(
            (
                f"- {row['symbol']} @ {row['provider']}: stake {row['staked_amount']}, "
                f"pending {row['pending_rewards_usd']:.2f} USD, unlock {unlock}, claim {claim}"
            )
        )
    return "\n".join(lines)


def format_action_explain(action: dict) -> str:
    return "\n".join(
        [
            f"Action #{action['id']}",
            f"Type: {action['action_type']}",
            f"Title: {action['title']}",
            f"Reason: {action['reason']}",
            f"Effect: {action['effect']}",
            f"Status: {action['status']}",
            f"Created: {action['created_at']}",
            f"Calculation: {action['calculation']}",
        ]
    )


def format_daily_digest(*, summary: dict, risk: dict, actions: list[dict], staking: list[dict]) -> str:
    lines = [
        "PocketQuant Daily Digest",
        f"Portfolio: {summary['total_value_usd']:.2f} USD (24h: n/a)",
        f"Risk: {risk['risk_mode']} | drawdown {risk['drawdown_pct']:.2%}",
        "Top actions:",
    ]
    if actions:
        for action in actions[:3]:
            lines.append(f"- #{action['id']} [{action['action_type']}] {action['title']}")
    else:
        lines.append("- No new actions")

    if staking:
        first = staking[0]
        lines.append(
            f"Staking signal: {first['symbol']} @ {first['provider']} pending {first['pending_rewards_usd']:.2f} USD"
        )
    else:
        lines.append("Staking signal: n/a")

    return "\n".join(lines)


def format_weekly_digest(*, summary: dict, actions_new: list[dict], done: int, postponed: int, dismissed: int) -> str:
    lines = [
        "PocketQuant Weekly Digest",
        f"Portfolio snapshot: {summary['total_value_usd']:.2f} USD",
        f"Action outcomes (7d proxy): done={done}, postponed={postponed}, dismissed={dismissed}",
        "Priority actions:",
    ]
    if actions_new:
        for action in actions_new[:3]:
            lines.append(f"- #{action['id']} [{action['action_type']}] {action['title']}")
    else:
        lines.append("- No new actions")
    return "\n".join(lines)
