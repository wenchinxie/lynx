"""Default configurations for backtest engine."""

# Default fees by market suffix
DEFAULT_FEES: dict[str, dict[str, float]] = {
    ".TW": {
        "commission_rate": 0.001425,     # 0.1425%
        "commission_discount": 0.6,       # 60% discount
        "tax_buy": 0.0,
        "tax_sell": 0.003,                # 0.3%
        "slippage": 0.001,                # 0.1%
    },
    ".US": {
        "commission_rate": 0.0,
        "commission_discount": 1.0,
        "tax_buy": 0.0,
        "tax_sell": 0.0,
        "slippage": 0.001,
    },
    "_default": {
        "commission_rate": 0.001,
        "commission_discount": 1.0,
        "tax_buy": 0.0,
        "tax_sell": 0.0,
        "slippage": 0.001,
    },
}

# Default lot sizes by market suffix
DEFAULT_LOT_SIZE: dict[str, int] = {
    ".TW": 1000,
    ".US": 1,
    "_default": 1,
}


def _get_suffix(symbol: str) -> str:
    """Extract market suffix from symbol (e.g., '.TW' from '2330.TW')."""
    if "." in symbol:
        return "." + symbol.split(".")[-1]
    return "_default"


def get_fees_for_symbol(
    symbol: str,
    custom_fees: dict[str, dict[str, float]] | None = None,
) -> dict[str, float]:
    """Get fee configuration for a symbol.

    Args:
        symbol: Stock symbol (e.g., '2330.TW')
        custom_fees: Optional custom fee overrides

    Returns:
        Dict with fee configuration
    """
    suffix = _get_suffix(symbol)

    # Start with default fees
    base_fees = DEFAULT_FEES.get(suffix, DEFAULT_FEES["_default"]).copy()

    # Apply custom overrides if provided
    if custom_fees:
        custom_for_suffix = custom_fees.get(suffix, {})
        base_fees.update(custom_for_suffix)

    return base_fees


def get_lot_size_for_symbol(
    symbol: str,
    custom_lot_size: dict[str, int] | None = None,
) -> int:
    """Get lot size for a symbol.

    Args:
        symbol: Stock symbol (e.g., '2330.TW')
        custom_lot_size: Optional custom lot size overrides

    Returns:
        Lot size as integer
    """
    suffix = _get_suffix(symbol)

    if custom_lot_size and suffix in custom_lot_size:
        return custom_lot_size[suffix]

    return DEFAULT_LOT_SIZE.get(suffix, DEFAULT_LOT_SIZE["_default"])
