import uuid
from decimal import Decimal
from types import SimpleNamespace

from app.services.holdings_service import HoldingsService


class FakePnLRepo:
    def latest_wallet_rows(self, _):
        return [SimpleNamespace(asset_symbol="BTC", wallet_balance=Decimal("1"), usd_value=Decimal("100000"))]


class FakeManualRepo:
    def active_for_user(self, _):
        return [SimpleNamespace(asset_type="gold", quantity=Decimal("1"), unit="oz", note="bar")]


class FakeMarketData:
    def get_metal_spot_prices_usd(self):
        return ({"gold": Decimal("2000")}, [])


class FakeHoldingsService(HoldingsService):
    def __init__(self):
        self.pnl_repo = FakePnLRepo()
        self.manual_repo = FakeManualRepo()
        self.market_data = FakeMarketData()


def test_holdings_valuation_with_manual_metals():
    service = FakeHoldingsService()
    result = service.get_holdings(uuid.uuid4())
    assert result.total_crypto_usd == Decimal("100000")
    assert result.total_manual_usd == Decimal("2000")
    assert result.total_portfolio_usd == Decimal("102000")
