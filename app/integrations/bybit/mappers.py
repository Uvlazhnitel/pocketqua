from datetime import datetime, timezone
from decimal import Decimal

from app.models.transactions_ledger import TransactionsLedger
from app.models.wallet_snapshot import WalletSnapshot


def _to_decimal(value: str | int | float | None) -> Decimal | None:
    if value in (None, ""):
        return None
    return Decimal(str(value))


def map_wallet_balance_to_snapshots(exchange_account_id, snapshot_ts: datetime, payload: dict) -> list[WalletSnapshot]:
    snapshots: list[WalletSnapshot] = []
    result = payload.get("result", {})
    now = datetime.now(timezone.utc)

    for account in result.get("list", []):
        account_type = account.get("accountType", "UNKNOWN")
        for coin_row in account.get("coin", []):
            wallet_balance = _to_decimal(coin_row.get("walletBalance"))
            if wallet_balance is None:
                continue
            locked = _to_decimal(coin_row.get("locked")) or Decimal("0")
            available = _to_decimal(coin_row.get("availableToWithdraw"))
            usd_value = _to_decimal(coin_row.get("usdValue"))

            snapshots.append(
                WalletSnapshot(
                    exchange_account_id=exchange_account_id,
                    snapshot_ts=snapshot_ts,
                    account_type=account_type,
                    asset_symbol=coin_row.get("coin", "UNKNOWN"),
                    wallet_balance=wallet_balance,
                    available_balance=available,
                    locked_balance=locked,
                    usd_value=usd_value,
                    source_payload=coin_row,
                    created_at=now,
                )
            )
    return snapshots


def map_transaction_log(exchange_account_id, rows: list[dict]) -> list[TransactionsLedger]:
    now = datetime.now(timezone.utc)
    events: list[TransactionsLedger] = []

    for row in rows:
        event_time_ms = int(row.get("transactionTime") or row.get("tradeTime") or 0)
        if event_time_ms <= 0:
            continue
        event_time = datetime.fromtimestamp(event_time_ms / 1000, tz=timezone.utc)

        qty = _to_decimal(row.get("change") or row.get("qty") or row.get("size") or "0") or Decimal("0")

        events.append(
            TransactionsLedger(
                exchange_account_id=exchange_account_id,
                external_event_id=str(row.get("id") or row.get("tradeId") or row.get("orderId") or f"txn-{event_time_ms}"),
                event_type=(row.get("type") or row.get("bizType") or "other").lower(),
                asset_symbol=(row.get("coin") or row.get("symbol") or "UNKNOWN").upper(),
                amount=qty,
                amount_usd=_to_decimal(row.get("cashFlow") or row.get("turnover")),
                fee_amount=_to_decimal(row.get("fee")),
                fee_asset_symbol=(row.get("feeCoin") or row.get("coin") or None),
                event_ts=event_time,
                source="bybit_transaction_log",
                source_payload=row,
                created_at=now,
            )
        )
    return events


def map_internal_transfers(exchange_account_id, rows: list[dict]) -> list[TransactionsLedger]:
    now = datetime.now(timezone.utc)
    events: list[TransactionsLedger] = []

    for row in rows:
        ts = int(row.get("timestamp") or row.get("transferTime") or 0)
        if ts <= 0:
            continue
        event_time = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        amount = _to_decimal(row.get("amount")) or Decimal("0")

        events.append(
            TransactionsLedger(
                exchange_account_id=exchange_account_id,
                external_event_id=str(row.get("transferId") or f"transfer-{ts}"),
                event_type="transfer",
                asset_symbol=(row.get("coin") or "UNKNOWN").upper(),
                amount=amount,
                amount_usd=None,
                fee_amount=None,
                fee_asset_symbol=None,
                event_ts=event_time,
                source="bybit_internal_transfer",
                source_payload=row,
                created_at=now,
            )
        )
    return events
