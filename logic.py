"""
Pure business logic and mathematical functions.

This module is intentionally separated from the Dash UI layer to allow
for isolated unit testing without requiring a web framework context.
"""

import pandas as pd

def calculate_compound_forecast(last_date: pd.Timestamp, last_value: float, horizon_months: int, monthly_growth_rate: float):
    """
    Calculate future values based on a compound monthly growth rate.

    Args:
        last_date (pd.Timestamp): The date of the last historical data point.
        last_value (float): The visitor volume of the last historical data point.
        horizon_months (int): The number of future months to project.
        monthly_growth_rate (float): The expected monthly growth percentage.

    Returns:
        tuple: A tuple containing two lists: (future_dates, future_values).
    """
    future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, horizon_months + 1)]
    future_values = []
    
    current_val = last_value
    growth_multiplier = 1 + (monthly_growth_rate / 100.0)
    
    for _ in range(horizon_months):
        current_val *= growth_multiplier
        future_values.append(current_val)
        
    return future_dates, future_values