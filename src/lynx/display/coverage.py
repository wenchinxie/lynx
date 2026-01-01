"""Stock coverage analysis for comparing strategy selections against watchlists.

This module provides functions for analyzing how well a strategy's selections
cover a user's watchlist or portfolio holdings (FR-036, FR-037).
"""

from dataclasses import dataclass


@dataclass
class CoverageAnalysis:
    """Results of comparing strategy selections against watchlists.

    Attributes:
        watchlist_held: Symbols in watchlist that strategy selected
        watchlist_missed: Symbols in watchlist that strategy did not select
        watchlist_coverage_pct: Percentage of watchlist symbols that were held
        portfolio_overlap: User holdings that strategy also selected
        portfolio_gaps: User holdings that strategy did not select
        portfolio_coverage_pct: Percentage of portfolio holdings that were held
    """

    watchlist_held: list[str]
    watchlist_missed: list[str]
    watchlist_coverage_pct: float
    portfolio_overlap: list[str]
    portfolio_gaps: list[str]
    portfolio_coverage_pct: float


def calculate_watchlist_coverage(
    strategy_symbols: list[str] | set[str],
    watchlist_symbols: list[str] | set[str],
) -> dict:
    """Calculate coverage of watchlist symbols by strategy selections.

    Args:
        strategy_symbols: Symbols selected by the strategy
        watchlist_symbols: Symbols in the user's watchlist

    Returns:
        Dict with held, missed, total, and coverage_pct

    Example:
        >>> strategy = ["2330", "2317", "2603"]
        >>> watchlist = ["2330", "2317", "2454", "3008"]
        >>> coverage = calculate_watchlist_coverage(strategy, watchlist)
        >>> coverage["coverage_pct"]
        0.5
    """
    strategy_set = set(strategy_symbols)
    watchlist_set = set(watchlist_symbols)

    held = sorted(strategy_set & watchlist_set)
    missed = sorted(watchlist_set - strategy_set)
    total = len(watchlist_set)

    coverage_pct = len(held) / total if total > 0 else 0.0

    return {
        "held": held,
        "missed": missed,
        "total": total,
        "coverage_pct": coverage_pct,
    }


def calculate_portfolio_coverage(
    strategy_symbols: list[str] | set[str],
    portfolio_symbols: list[str] | set[str],
) -> dict:
    """Calculate overlap between strategy selections and portfolio holdings.

    Args:
        strategy_symbols: Symbols selected by the strategy
        portfolio_symbols: Symbols in the user's portfolio

    Returns:
        Dict with overlap, gaps, total, and coverage_pct

    Example:
        >>> strategy = ["2330", "2317", "2603"]
        >>> portfolio = ["2330", "2317", "2882"]
        >>> coverage = calculate_portfolio_coverage(strategy, portfolio)
        >>> coverage["coverage_pct"]
        0.6666666666666666
    """
    strategy_set = set(strategy_symbols)
    portfolio_set = set(portfolio_symbols)

    overlap = sorted(strategy_set & portfolio_set)
    gaps = sorted(portfolio_set - strategy_set)
    total = len(portfolio_set)

    coverage_pct = len(overlap) / total if total > 0 else 0.0

    return {
        "overlap": overlap,
        "gaps": gaps,
        "total": total,
        "coverage_pct": coverage_pct,
    }


def calculate_coverage(
    strategy_symbols: list[str] | set[str],
    watchlist_symbols: list[str] | set[str] | None = None,
    portfolio_symbols: list[str] | set[str] | None = None,
) -> CoverageAnalysis:
    """Calculate complete coverage analysis for a strategy.

    Args:
        strategy_symbols: Symbols selected by the strategy
        watchlist_symbols: Optional list of watchlist symbols
        portfolio_symbols: Optional list of portfolio symbols

    Returns:
        CoverageAnalysis dataclass with all coverage metrics

    Example:
        >>> strategy = ["2330", "2317", "2603"]
        >>> watchlist = ["2330", "2317", "2454"]
        >>> portfolio = ["2330", "2882"]
        >>> coverage = calculate_coverage(strategy, watchlist, portfolio)
        >>> coverage.watchlist_coverage_pct
        0.6666666666666666
    """
    # Calculate watchlist coverage
    if watchlist_symbols:
        watchlist_result = calculate_watchlist_coverage(
            strategy_symbols, watchlist_symbols
        )
        watchlist_held = watchlist_result["held"]
        watchlist_missed = watchlist_result["missed"]
        watchlist_coverage_pct = watchlist_result["coverage_pct"]
    else:
        watchlist_held = []
        watchlist_missed = []
        watchlist_coverage_pct = 0.0

    # Calculate portfolio coverage
    if portfolio_symbols:
        portfolio_result = calculate_portfolio_coverage(
            strategy_symbols, portfolio_symbols
        )
        portfolio_overlap = portfolio_result["overlap"]
        portfolio_gaps = portfolio_result["gaps"]
        portfolio_coverage_pct = portfolio_result["coverage_pct"]
    else:
        portfolio_overlap = []
        portfolio_gaps = []
        portfolio_coverage_pct = 0.0

    return CoverageAnalysis(
        watchlist_held=watchlist_held,
        watchlist_missed=watchlist_missed,
        watchlist_coverage_pct=watchlist_coverage_pct,
        portfolio_overlap=portfolio_overlap,
        portfolio_gaps=portfolio_gaps,
        portfolio_coverage_pct=portfolio_coverage_pct,
    )
