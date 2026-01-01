"""Tests for trading cost calculations."""

import pytest
from lynx.backtest.costs import calculate_buy_cost, calculate_sell_revenue


class TestCalculateBuyCost:
    def test_basic_buy_cost(self):
        # price=100, shares=1000, commission=0.1%, slippage=0.1%
        fees = {
            "commission_rate": 0.001,
            "commission_discount": 1.0,
            "slippage": 0.001,
        }
        cost = calculate_buy_cost(price=100.0, shares=1000, fees=fees)
        # 100 * 1000 * (1 + 0.001 + 0.001) = 100,200
        assert cost == pytest.approx(100200.0)

    def test_tw_buy_cost_with_discount(self):
        # Taiwan market with broker discount
        fees = {
            "commission_rate": 0.001425,
            "commission_discount": 0.6,
            "slippage": 0.001,
        }
        cost = calculate_buy_cost(price=580.0, shares=1000, fees=fees)
        # 580 * 1000 * (1 + 0.001425*0.6 + 0.001)
        # = 580000 * (1 + 0.000855 + 0.001)
        # = 580000 * 1.001855
        # = 581075.9
        expected = 580000 * (1 + 0.001425 * 0.6 + 0.001)
        assert cost == pytest.approx(expected)

    def test_zero_commission(self):
        fees = {
            "commission_rate": 0.0,
            "commission_discount": 1.0,
            "slippage": 0.001,
        }
        cost = calculate_buy_cost(price=100.0, shares=100, fees=fees)
        # 100 * 100 * (1 + 0 + 0.001) = 10010
        assert cost == pytest.approx(10010.0)


class TestCalculateSellRevenue:
    def test_basic_sell_revenue(self):
        fees = {
            "commission_rate": 0.001,
            "commission_discount": 1.0,
            "tax_sell": 0.0,
            "slippage": 0.001,
        }
        revenue = calculate_sell_revenue(price=100.0, shares=1000, fees=fees)
        # 100 * 1000 * (1 - 0.001 - 0 - 0.001) = 99800
        assert revenue == pytest.approx(99800.0)

    def test_tw_sell_revenue_with_tax(self):
        # Taiwan market with sell tax
        fees = {
            "commission_rate": 0.001425,
            "commission_discount": 0.6,
            "tax_sell": 0.003,
            "slippage": 0.001,
        }
        revenue = calculate_sell_revenue(price=600.0, shares=1000, fees=fees)
        # 600 * 1000 * (1 - 0.001425*0.6 - 0.003 - 0.001)
        # = 600000 * (1 - 0.000855 - 0.003 - 0.001)
        # = 600000 * 0.995145
        expected = 600000 * (1 - 0.001425 * 0.6 - 0.003 - 0.001)
        assert revenue == pytest.approx(expected)

    def test_us_sell_no_tax(self):
        fees = {
            "commission_rate": 0.0,
            "commission_discount": 1.0,
            "tax_sell": 0.0,
            "slippage": 0.001,
        }
        revenue = calculate_sell_revenue(price=150.0, shares=100, fees=fees)
        # 150 * 100 * (1 - 0 - 0 - 0.001) = 14985
        assert revenue == pytest.approx(14985.0)
