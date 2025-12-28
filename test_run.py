#!/usr/bin/env python3
"""Quick test script to verify metrics implementation."""
import sys
sys.path.insert(0, '/home/hanson/lynx/src')

import pandas as pd
from datetime import datetime
from lynx.metrics import calculate_all

# Create sample trades
trades = pd.DataFrame({
    "entry_date": [
        datetime(2024, 1, 1),
        datetime(2024, 2, 1),
        datetime(2024, 3, 1),
    ],
    "exit_date": [
        datetime(2024, 1, 10),
        datetime(2024, 2, 15),
        datetime(2024, 3, 5),
    ],
    "return": [0.05, -0.02, 0.03],
})

# Calculate all metrics
metrics = calculate_all(trades)

print("Metrics calculation test:")
print("-" * 50)
for key, value in metrics.items():
    print(f"{key:30} {value:.6f}" if isinstance(value, float) else f"{key:30} {value}")
print("-" * 50)
print("Test completed successfully!")
