from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.db import models
from backend.app.db.schemas import PositionUpsertIn, PriceUpsertIn, StrategyUpsertIn


def get_or_create_asset(
    db: Session, symbol: str, name: str, asset_class: models.AssetClass
) -> models.Asset:
    asset = db.scalar(select(models.Asset).where(models.Asset.symbol == symbol))
    if asset:
        asset.name = name
        asset.asset_class = asset_class
        return asset

    asset = models.Asset(symbol=symbol, name=name, asset_class=asset_class)
    db.add(asset)
    db.flush()
    return asset


def upsert_position(db: Session, payload: PositionUpsertIn) -> models.Position:
    asset = get_or_create_asset(
        db,
        symbol=payload.symbol,
        name=payload.name,
        asset_class=models.AssetClass(payload.asset_class.value),
    )

    position = db.scalar(
        select(models.Position).where(
            models.Position.asset_id == asset.id,
            models.Position.account == payload.account,
        )
    )

    if position:
        position.amount = payload.amount
        position.avg_cost_eur = payload.avg_cost_eur
        position.updated_at = datetime.now(timezone.utc)
        return position

    position = models.Position(
        asset_id=asset.id,
        account=payload.account,
        amount=payload.amount,
        avg_cost_eur=payload.avg_cost_eur,
        updated_at=datetime.now(timezone.utc),
    )
    db.add(position)
    db.flush()
    return position


def upsert_price(db: Session, payload: PriceUpsertIn) -> models.Price:
    asset = db.scalar(select(models.Asset).where(models.Asset.symbol == payload.symbol))
    if not asset:
        raise ValueError(f"asset {payload.symbol} does not exist")

    price = db.scalar(select(models.Price).where(models.Price.asset_id == asset.id))
    if price:
        price.price_eur = payload.price_eur
        price.as_of = datetime.now(timezone.utc)
        return price

    price = models.Price(
        asset_id=asset.id,
        price_eur=payload.price_eur,
        as_of=datetime.now(timezone.utc),
    )
    db.add(price)
    db.flush()
    return price


def set_active_strategy(db: Session, payload: StrategyUpsertIn) -> models.Strategy:
    db.query(models.Strategy).update({models.Strategy.is_active: False})

    strategy = models.Strategy(
        name=payload.name,
        base_currency=payload.base_currency,
        is_active=True,
        dca_enabled=payload.dca_enabled,
        dca_interval_days=payload.dca_interval_days,
    )
    db.add(strategy)
    db.flush()

    for target in payload.targets:
        asset = get_or_create_asset(
            db,
            symbol=target.symbol,
            name=target.name,
            asset_class=models.AssetClass(target.asset_class.value),
        )
        db.add(
            models.StrategyTarget(
                strategy_id=strategy.id,
                asset_id=asset.id,
                target_weight=target.target_weight,
                band_min=target.band_min,
                band_max=target.band_max,
            )
        )

    db.flush()
    return strategy


def get_active_strategy(db: Session) -> models.Strategy | None:
    return db.scalar(select(models.Strategy).where(models.Strategy.is_active.is_(True)))


def get_strategy_targets(db: Session, strategy_id: int) -> list[models.StrategyTarget]:
    return list(
        db.scalars(
            select(models.StrategyTarget).where(models.StrategyTarget.strategy_id == strategy_id)
        )
    )


def create_recommendation(
    db: Session,
    strategy_id: int,
    action_type: models.ActionType,
    title: str,
    reason: str,
    payload_json: dict,
) -> models.Recommendation:
    rec = models.Recommendation(
        strategy_id=strategy_id,
        action_type=action_type,
        title=title,
        reason=reason,
        payload_json=payload_json,
        status=models.RecommendationStatus.NEW,
    )
    db.add(rec)
    db.flush()
    return rec


def list_recommendations(db: Session) -> list[models.Recommendation]:
    return list(db.scalars(select(models.Recommendation).order_by(desc(models.Recommendation.created_at))))
