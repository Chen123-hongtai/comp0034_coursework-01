"""Provide an interactive forecasting interface for visitor volumes."""

from __future__ import annotations

import dash
from dash import Input, Output, callback, dcc, html
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from logic import calculate_compound_forecast
from services.api_client import ApiUnavailableError, get_scenario_history, get_scenario_markets


dash.register_page(__name__, name="Scenario Simulator")


historical_dates = pd.date_range(start="2022-01-01", end="2023-12-01", freq="MS")
mock_history = pd.DataFrame(
    {
        "Date": historical_dates,
        "Visitors": np.linspace(50000, 150000, len(historical_dates))
        + np.random.default_rng(42).normal(0, 5000, len(historical_dates)),
        "Market": "Total Inbound",
    }
)


def _load_markets() -> list[str]:
    try:
        markets = get_scenario_markets()
        if not markets:
            raise ApiUnavailableError("No market options from API")
        return markets
    except ApiUnavailableError:
        return ["Total Inbound", "Southeast Asia", "Europe"]


market_options = _load_markets()


layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H2("Scenario Simulator", className="mb-2"),
                        html.P(
                            "Adjust the parameters below to forecast future visitor volumes and assess capacity risks "
                            "for the upcoming 6 to 12 months.",
                            className="text-muted mb-4",
                        ),
                    ]
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5("Simulation Parameters", className="card-title mb-4"),
                                html.Label("Target Market:", className="font-weight-bold"),
                                dcc.Dropdown(
                                    id="sim-market-dropdown",
                                    options=[{"label": m, "value": m} for m in market_options],
                                    value="Total Inbound" if "Total Inbound" in market_options else market_options[0],
                                    clearable=False,
                                    className="mb-4",
                                ),
                                html.Label("Projection Horizon (Months):", className="font-weight-bold"),
                                dcc.Slider(
                                    id="sim-horizon-slider",
                                    min=3,
                                    max=12,
                                    step=1,
                                    value=6,
                                    marks={i: str(i) for i in range(3, 13, 3)},
                                    className="mb-4",
                                ),
                                html.Label("Expected Monthly Growth Rate (%):", className="font-weight-bold"),
                                dcc.Slider(
                                    id="sim-growth-slider",
                                    min=-5.0,
                                    max=10.0,
                                    step=0.5,
                                    value=2.0,
                                    marks={i: f"{i}%" for i in range(-5, 11, 5)},
                                    tooltip={"placement": "bottom", "always_visible": True},
                                    className="mb-4",
                                ),
                                html.Hr(),
                                html.Small(
                                    "Note: The simulation applies a compound growth rate to the last observed data point.",
                                    className="text-muted",
                                ),
                            ]
                        ),
                        className="shadow-sm border-0 h-100",
                    ),
                    width=4,
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            dbc.CardBody([html.H5("Forecast vs Actuals", className="card-title"), dcc.Graph(id="sim-forecast-chart")]),
                            className="shadow-sm border-0 mb-4",
                        ),
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5("Simulation Output Summary", className="card-title"),
                                    html.Div(id="sim-summary-text", className="lead text-primary"),
                                ]
                            ),
                            className="shadow-sm border-0 bg-light",
                        ),
                    ],
                    width=8,
                ),
            ]
        ),
    ]
)


def _history_for_market(market: str) -> pd.DataFrame:
    try:
        payload = get_scenario_history(market)
        points = payload.get("points", [])
        if not points:
            raise ApiUnavailableError("No scenario history points returned")
        df = pd.DataFrame(points)
        df["Date"] = pd.to_datetime(df["date"])
        df["Visitors"] = df["visitors"].astype(float)
        return df[["Date", "Visitors"]]
    except ApiUnavailableError:
        return mock_history[["Date", "Visitors"]].copy()


@callback(
    [Output("sim-forecast-chart", "figure"), Output("sim-summary-text", "children")],
    [Input("sim-market-dropdown", "value"), Input("sim-horizon-slider", "value"), Input("sim-growth-slider", "value")],
)
def update_simulation(market: str, horizon_months: int, monthly_growth_rate: float):
    df_hist = _history_for_market(market)

    last_date = df_hist["Date"].iloc[-1]
    last_value = float(df_hist["Visitors"].iloc[-1])

    future_dates, future_values = calculate_compound_forecast(last_date, last_value, horizon_months, monthly_growth_rate)

    forecast_dates = [last_date] + future_dates
    forecast_vals = [last_value] + future_values

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_hist["Date"],
            y=df_hist["Visitors"],
            mode="lines+markers",
            name="Historical Actuals",
            line=dict(color="#2C3E50", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=forecast_vals,
            mode="lines+markers",
            name="Simulated Forecast",
            line=dict(color="#E74C3C", width=2, dash="dash"),
        )
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    final_projected_value = forecast_vals[-1]
    net_change = final_projected_value - last_value

    summary_msg = (
        f"By the end of the {horizon_months}-month horizon, {market} visitors are projected to reach "
        f"{int(final_projected_value):,}. This is a net change of {int(net_change):,} visitors "
        f"compared to current levels based on a {monthly_growth_rate}% monthly growth rate."
    )

    return fig, summary_msg