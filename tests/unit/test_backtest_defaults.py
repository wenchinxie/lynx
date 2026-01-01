"""Tests for backtest default configurations."""

import pytest
from lynx.backtest.defaults import (
    DEFAULT_FEES,
    DEFAULT_LOT_SIZE,
    get_fees_for_symbol,
    get_lot_size_for_symbol,
)


class TestDefaultFees:
    def test_tw_fees_exist(self):
        assert ".TW" in DEFAULT_FEES
        tw_fees = DEFAULT_FEES[".TW"]
        assert tw_fees["commission_rate"] == 0.001425
        assert tw_fees["commission_discount"] == 0.6
        assert tw_fees["tax_buy"] == 0.0
        assert tw_fees["tax_sell"] == 0.003
        assert tw_fees["slippage"] == 0.001

    def test_us_fees_exist(self):
        assert ".US" in DEFAULT_FEES
        us_fees = DEFAULT_FEES[".US"]
        assert us_fees["commission_rate"] == 0.0
        assert us_fees["tax_sell"] == 0.0

    def test_default_fees_exist(self):
        assert "_default" in DEFAULT_FEES


class TestDefaultLotSize:
    def test_tw_lot_size(self):
        assert DEFAULT_LOT_SIZE[".TW"] == 1000

    def test_us_lot_size(self):
        assert DEFAULT_LOT_SIZE[".US"] == 1

    def test_default_lot_size(self):
        assert DEFAULT_LOT_SIZE["_default"] == 1


class TestGetFeesForSymbol:
    def test_tw_symbol(self):
        fees = get_fees_for_symbol("2330.TW")
        assert fees["commission_rate"] == 0.001425
        assert fees["tax_sell"] == 0.003

    def test_us_symbol(self):
        fees = get_fees_for_symbol("AAPL.US")
        assert fees["commission_rate"] == 0.0
        assert fees["tax_sell"] == 0.0

    def test_unknown_suffix_uses_default(self):
        fees = get_fees_for_symbol("ABC.UK")
        assert fees == DEFAULT_FEES["_default"]

    def test_no_suffix_uses_default(self):
        fees = get_fees_for_symbol("2330")
        assert fees == DEFAULT_FEES["_default"]

    def test_custom_fees_override(self):
        custom = {".TW": {"commission_discount": 0.28}}
        fees = get_fees_for_symbol("2330.TW", custom)
        assert fees["commission_discount"] == 0.28
        assert fees["commission_rate"] == 0.001425  # inherited from default


class TestGetLotSizeForSymbol:
    def test_tw_symbol(self):
        lot_size = get_lot_size_for_symbol("2330.TW")
        assert lot_size == 1000

    def test_us_symbol(self):
        lot_size = get_lot_size_for_symbol("AAPL.US")
        assert lot_size == 1

    def test_custom_lot_size(self):
        custom = {".TW": 500}
        lot_size = get_lot_size_for_symbol("2330.TW", custom)
        assert lot_size == 500
