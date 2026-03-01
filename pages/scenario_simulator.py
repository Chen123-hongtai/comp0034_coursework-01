"""
Provide an interactive forecasting interface for visitor volumes.

This module contains a simulation tool that allows users to adjust target
markets, projection horizons, and expected growth rates. It calculates
future trends based on historical data and displays a comparative chart.
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from logic import calculate_compound_forecast

# Register this page with the Dash app
dash.register_page(__name__, name='Scenario Simulator')

# ==========================================
# Pure Functions for Business Logic (Decoupled for Unit Testing)
# ==========================================
def calculate_compound_forecast(last_date: pd.Timestamp, last_value: float, horizon_months: int, monthly_growth_rate: float):
    """
    Calculate future values based on a compound monthly growth rate.

    This is a pure function decoupled from Dash callbacks and database context, 
    making it easy to isolate for unit testing (addressing CW2 feedback).

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

# ==========================================
# Mock Historical Data
# ==========================================
historical_dates = pd.date_range(start="2022-01-01", end="2023-12-01", freq="MS")
mock_history = pd.DataFrame({
    'Date': historical_dates,
    'Visitors': np.linspace(50000, 150000, len(historical_dates)) + np.random.normal(0, 5000, len(historical_dates)),
    'Market': 'Total Inbound'
})

# ==========================================
# Page Layout
# ==========================================
layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.H2("Scenario Simulator", className="mb-2"),
            html.P(
                "Adjust the parameters below to forecast future visitor volumes and assess capacity risks "
                "for the upcoming 6 to 12 months.",
                className="text-muted mb-4"
            )
        ])
    ]),

    dbc.Row([
        # Left Column: Simulation Controls
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H5("Simulation Parameters", className="card-title mb-4"),
                    
                    html.Label("Target Market:", className="font-weight-bold"),
                    dcc.Dropdown(
                        id='sim-market-dropdown',
                        options=[{'label': 'Total Inbound', 'value': 'Total Inbound'},
                                 {'label': 'Southeast Asia', 'value': 'Southeast Asia'},
                                 {'label': 'Europe', 'value': 'Europe'}],
                        value='Total Inbound',
                        clearable=False,
                        className="mb-4"
                    ),
                    
                    html.Label("Projection Horizon (Months):", className="font-weight-bold"),
                    dcc.Slider(
                        id='sim-horizon-slider',
                        min=3, max=12, step=1, value=6,
                        marks={i: str(i) for i in range(3, 13, 3)},
                        className="mb-4"
                    ),
                    
                    html.Label("Expected Monthly Growth Rate (%):", className="font-weight-bold"),
                    dcc.Slider(
                        id='sim-growth-slider',
                        min=-5.0, max=10.0, step=0.5, value=2.0,
                        marks={i: f"{i}%" for i in range(-5, 11, 5)},
                        tooltip={"placement": "bottom", "always_visible": True},
                        className="mb-4"
                    ),
                    
                    html.Hr(),
                    html.Small(
                        "Note: The simulation applies a compound growth rate to the last observed data point.",
                        className="text-muted"
                    )
                ]),
                className="shadow-sm border-0 h-100"
            ),
            width=4
        ),

        # Right Column: Output Chart and Insights
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    html.H5("Forecast vs Actuals", className="card-title"),
                    dcc.Graph(id='sim-forecast-chart')
                ]),
                className="shadow-sm border-0 mb-4"
            ),
            
            dbc.Card(
                dbc.CardBody([
                    html.H5("Simulation Output Summary", className="card-title"),
                    html.Div(id='sim-summary-text', className="lead text-primary")
                ]),
                className="shadow-sm border-0 bg-light"
            )
        ], width=8)
    ])
])

# ==========================================
# Callbacks (Interactivity / Logic)
# ==========================================
@callback(
    [Output('sim-forecast-chart', 'figure'),
     Output('sim-summary-text', 'children')],
    [Input('sim-market-dropdown', 'value'),
     Input('sim-horizon-slider', 'value'),
     Input('sim-growth-slider', 'value')]
)
def update_simulation(market: str, horizon_months: int, monthly_growth_rate: float):
    """
    Calculate the forecasted visitor volume and update the simulation chart.

    Applies a compound monthly growth rate to the last observed historical
    data point to generate future data points for the specified horizon.
    Delegates the core calculation to a pure function for better testability.

    Args:
        market (str): The target market selected for simulation.
        horizon_months (int): The number of future months to project (3 to 12).
        monthly_growth_rate (float): The expected monthly growth percentage.

    Returns:
        tuple: A Plotly graph object figure containing both historical and 
               simulated lines, and a text summary of the projection.
    """
    df_hist = mock_history.copy()
    
    last_date = df_hist['Date'].iloc[-1]
    last_value = df_hist['Visitors'].iloc[-1]
    
    # 🌟 CORE CHANGE: Calling the decoupled pure function here!
    future_dates, future_values = calculate_compound_forecast(
        last_date, last_value, horizon_months, monthly_growth_rate
    )
        
    forecast_dates = [last_date] + future_dates
    forecast_vals = [last_value] + future_values
    
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_hist['Date'], y=df_hist['Visitors'],
        mode='lines+markers',
        name='Historical Actuals',
        line=dict(color='#2C3E50', width=2)
    ))

    fig.add_trace(go.Scatter(
        x=forecast_dates, y=forecast_vals,
        mode='lines+markers',
        name='Simulated Forecast',
        line=dict(color='#E74C3C', width=2, dash='dash')
    ))

    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    final_projected_value = forecast_vals[-1]
    net_change = final_projected_value - last_value
    
    summary_msg = f"By the end of the {horizon_months}-month horizon, {market} visitors are projected to reach " \
                  f"{int(final_projected_value):,}. This is a net change of {int(net_change):,} visitors " \
                  f"compared to current levels based on a {monthly_growth_rate}% monthly growth rate."

    return fig, summary_msg