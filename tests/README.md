# Lynx Tests

This directory contains all tests for the Lynx backtest tracking system.

## Directory Structure

```
tests/
├── conftest.py          # Shared pytest fixtures
├── test_fixtures.py     # Tests to verify fixtures work correctly
├── unit/                # Unit tests
├── integration/         # Integration tests
└── fixtures/            # Test data files
    └── sample_trades.csv
```

## Available Fixtures

All fixtures are defined in `conftest.py` and are automatically available to all test files.

### `temp_data_dir`
Creates a temporary directory for test data that is automatically cleaned up after tests.

**Usage:**
```python
def test_something(temp_data_dir):
    data_file = temp_data_dir / "test.csv"
    # ... use temp_data_dir
```

### `sample_trades_df`
Returns a DataFrame with 5 sample trades for testing.

**Columns:** symbol, entry_date, exit_date, entry_price, exit_price, return

**Usage:**
```python
def test_trade_analysis(sample_trades_df):
    assert len(sample_trades_df) == 5
    # ... test your functions
```

### `sample_signal_df`
Returns a DataFrame with 10 days of boolean signals for 3 symbols.

**Columns:** 2330, 2317, 2454 (Taiwan stock symbols)
**Index:** DatetimeIndex with 10 days starting from 2024-01-01

**Usage:**
```python
def test_signal_processing(sample_signal_df):
    assert sample_signal_df.shape == (10, 3)
    # ... test your signal logic
```

### `sample_price_df`
Returns a DataFrame with 10 days of price data for 3 symbols.

**Columns:** 2330, 2317, 2454 (Taiwan stock symbols)
**Index:** DatetimeIndex with 10 days starting from 2024-01-01

**Usage:**
```python
def test_price_calculation(sample_price_df):
    assert sample_price_df.shape == (10, 3)
    # ... test your price calculations
```

### `empty_trades_df`
Returns an empty DataFrame with the correct trade schema for edge case testing.

**Usage:**
```python
def test_empty_data_handling(empty_trades_df):
    assert len(empty_trades_df) == 0
    # ... test your edge case handling
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=lynx --cov-report=html
```

### Run specific test file
```bash
pytest tests/unit/test_storage.py
```

### Run specific test function
```bash
pytest tests/unit/test_storage.py::test_save_trades
```

### Run tests matching a pattern
```bash
pytest -k "signal"
```

## Writing Tests

1. Create test files with `test_` prefix
2. Create test functions with `test_` prefix
3. Use fixtures by adding them as function parameters
4. Follow the Arrange-Act-Assert pattern

**Example:**
```python
def test_calculate_returns(sample_trades_df):
    # Arrange
    trades = sample_trades_df.copy()

    # Act
    result = calculate_returns(trades)

    # Assert
    assert result is not None
    assert len(result) == len(trades)
```

## Test Configuration

Test configuration is defined in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-v --cov=lynx --cov-report=term-missing"
```

This configuration:
- Sets the test discovery path to `tests/`
- Adds `src/` to Python path for imports
- Enables verbose output and coverage reporting
