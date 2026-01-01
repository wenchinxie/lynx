"""Trading cost calculations for backtest engine."""


def calculate_buy_cost(
    price: float,
    shares: int,
    fees: dict[str, float],
) -> float:
    """Calculate total cost to buy shares including fees.

    Args:
        price: Price per share
        shares: Number of shares to buy
        fees: Fee configuration dict

    Returns:
        Total cost including commission and slippage
    """
    commission_rate = fees.get("commission_rate", 0.0)
    commission_discount = fees.get("commission_discount", 1.0)
    slippage = fees.get("slippage", 0.0)

    effective_commission = commission_rate * commission_discount
    multiplier = 1 + effective_commission + slippage

    return price * shares * multiplier


def calculate_sell_revenue(
    price: float,
    shares: int,
    fees: dict[str, float],
) -> float:
    """Calculate net revenue from selling shares after fees.

    Args:
        price: Price per share
        shares: Number of shares to sell
        fees: Fee configuration dict

    Returns:
        Net revenue after commission, tax, and slippage
    """
    commission_rate = fees.get("commission_rate", 0.0)
    commission_discount = fees.get("commission_discount", 1.0)
    tax_sell = fees.get("tax_sell", 0.0)
    slippage = fees.get("slippage", 0.0)

    effective_commission = commission_rate * commission_discount
    multiplier = 1 - effective_commission - tax_sell - slippage

    return price * shares * multiplier
