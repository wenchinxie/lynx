"""Data module exceptions."""


class DataFetchError(Exception):
    """Raised when data fetching fails."""

    pass


class InvalidSymbolError(Exception):
    """Raised when symbol is not found or invalid."""

    pass
