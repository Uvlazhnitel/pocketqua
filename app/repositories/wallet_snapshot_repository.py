from sqlalchemy.orm import Session

from app.models.wallet_snapshot import WalletSnapshot


class WalletSnapshotRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_many(self, snapshots: list[WalletSnapshot]) -> None:
        self.db.add_all(snapshots)
