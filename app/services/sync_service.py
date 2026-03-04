import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import get_settings
from app.integrations.bybit.client import BybitClient
from app.integrations.bybit.mappers import map_internal_transfers, map_transaction_log, map_wallet_balance_to_snapshots
from app.models.exchange_account import ExchangeAccount
from app.repositories.exchange_account_repository import ExchangeAccountRepository
from app.repositories.ledger_repository import LedgerRepository
from app.repositories.wallet_snapshot_repository import WalletSnapshotRepository
from app.security import decrypt_secret

logger = logging.getLogger(__name__)


class SyncService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.accounts_repo = ExchangeAccountRepository(db)
        self.snap_repo = WalletSnapshotRepository(db)
        self.ledger_repo = LedgerRepository(db)

    def run(self) -> int:
        accounts = self.accounts_repo.get_active_bybit_accounts()
        if not accounts:
            return 0

        failures = []
        for account in accounts:
            try:
                self._sync_single(account.id)
            except Exception as exc:
                self.db.rollback()
                failures.append(exc)

        if failures:
            raise RuntimeError(f"Sync completed with {len(failures)} failure(s): {failures[0]}")

        return len(accounts)

    def _sync_single(self, account_id: uuid.UUID) -> None:
        account = self.db.get(ExchangeAccount, account_id)
        if account is None:
            return

        api_key = decrypt_secret(account.api_key_encrypted)
        api_secret = decrypt_secret(account.api_secret_encrypted)
        client = BybitClient(
            base_url=self.settings.bybit_base_url,
            api_key=api_key,
            api_secret=api_secret,
            recv_window=self.settings.bybit_recv_window,
        )

        now = datetime.now(timezone.utc)
        snapshot_ts = now
        last_sync = account.last_sync_at

        if last_sync is None:
            start = now - timedelta(days=90)
        else:
            start = last_sync - timedelta(minutes=10)

        start_ms = int(start.timestamp() * 1000)
        end_ms = int(now.timestamp() * 1000)

        logger.info("sync_account_start", extra={"account_id": str(account.id), "start_ms": start_ms, "end_ms": end_ms})

        wallet_payload = client.get_wallet_balance()
        snapshots = map_wallet_balance_to_snapshots(account.id, snapshot_ts, wallet_payload)

        tx_rows = client.get_transaction_log(start_ms=start_ms, end_ms=end_ms)
        transfer_rows = client.get_internal_transfers(start_ms=start_ms, end_ms=end_ms)

        tx_events = map_transaction_log(account.id, tx_rows)
        transfer_events = map_internal_transfers(account.id, transfer_rows)

        self.snap_repo.add_many(snapshots)
        _ = self.ledger_repo.insert_idempotent(tx_events + transfer_events)
        self.accounts_repo.set_last_sync(account, now)
        self.db.commit()

        logger.info(
            "sync_account_success",
            extra={
                "account_id": str(account.id),
                "snapshots": len(snapshots),
                "transactions": len(tx_events),
                "transfers": len(transfer_events),
            },
        )
