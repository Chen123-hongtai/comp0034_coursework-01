"""
Unit test suite for isolated business logic functions.

This module contains tests for the pure mathematical forecasting functions
that have been decoupled from the Dash UI callbacks. This directly addresses
the need for isolated unit testing independent of the database or web framework.
"""

import pytest
import pandas as pd
from logic import calculate_compound_forecast

# ==========================================
# Unit Tests for Forecasting Logic
# ==========================================

def test_calculate_compound_forecast_positive_growth():
    """
    Test the forecast calculation with a positive monthly growth rate.
    
    Ensures that a 10% monthly growth over 3 months applied to a base
    value of 100 correctly compounds to 110, 121, and 133.1, and that
    the generated dates are exactly one month apart.
    """
    # GIVEN: Initial parameters
    start_date = pd.Timestamp('2023-12-01')
    start_value = 100.0
    horizon = 3
    growth_rate = 10.0  # 10%
    
    # WHEN: The forecast function is called
    future_dates, future_values = calculate_compound_forecast(
        last_date=start_date,
        last_value=start_value,
        horizon_months=horizon,
        monthly_growth_rate=growth_rate
    )
    
    # THEN: Verify the results
    assert len(future_dates) == 3
    assert len(future_values) == 3
    
    # Check date increments (Jan, Feb, Mar 2024)
    assert future_dates[0] == pd.Timestamp('2024-01-01')
    assert future_dates[2] == pd.Timestamp('2024-03-01')
    
    # Check compound values: 100 -> 110 -> 121 -> 133.1
    assert round(future_values[0], 2) == 110.00
    assert round(future_values[1], 2) == 121.00
    assert round(future_values[2], 2) == 133.10


def test_calculate_compound_forecast_zero_growth():
    """
    Test the forecast calculation with a zero growth rate.
    
    Ensures that when the growth rate is 0%, the projected values remain
    exactly the same as the initial starting value across the horizon.
    """
    start_date = pd.Timestamp('2024-01-01')
    start_value = 5000.0
    horizon = 6
    growth_rate = 0.0  # 0%
    
    future_dates, future_values = calculate_compound_forecast(
        last_date=start_date,
        last_value=start_value,
        horizon_months=horizon,
        monthly_growth_rate=growth_rate
    )
    
    assert len(future_values) == 6
    # All future values should perfectly match the start value
    assert all(val == 5000.0 for val in future_values)


def test_calculate_compound_forecast_negative_growth():
    """
    Test the forecast calculation with a negative monthly growth rate (decline).
    
    Ensures that a negative percentage correctly reduces the base value over time.
    """
    start_date = pd.Timestamp('2024-01-01')
    start_value = 1000.0
    horizon = 2
    growth_rate = -50.0  # -50% (halving each month)
    
    future_dates, future_values = calculate_compound_forecast(
        last_date=start_date,
        last_value=start_value,
        horizon_months=horizon,
        monthly_growth_rate=growth_rate
    )
    
    assert len(future_values) == 2
    # 1000 -> 500 -> 250
    assert future_values[0] == 500.0
    assert future_values[1] == 250.0