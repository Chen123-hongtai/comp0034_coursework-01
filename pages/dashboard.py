"""Render the main dashboard page for tourism analytics."""

from __future__ import annotations

import dash
from dash import Input, Output, callback, dcc, html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

from services.api_client import ApiUnavailableError, get_dashboard_summary, get_regions


dash.register_page(__name__, path="/", name="Dashboard")


dates = pd.date_range(start="2023-01-01", periods=12, freq="ME")
mock_data = pd.DataFrame(
    {
        "Date": dates.tolist() * 2,
        "Visitors": [
            100,
            120,
            150,
            130,
            160,
            180,
            200,
            210,
            190,
            220,
            240,
            250,
        ]
        + [80, 90, 110, 100, 120, 140, 150, 160, 140, 170, 190, 200],
        "Region": ["Southeast Asia"] * 12 + ["Europe"] * 12,
    }
)


def _region_options() -> tuple[list[dict], str]:
    try:
        regions = get_regions()
        if not regions:
            raise ApiUnavailableError("No region data returned")
        return [{"label": region, "value": region} for region in regions], regions[0]
    except ApiUnavailableError:
        regions = sorted(mock_data["Region"].unique().tolist())
        return [{"label": region, "value": region} for region in regions], "Southeast Asia"


def create_kpi_card(title: str, id_name: str) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody(
            [
                html.H6(title, className="card-title text-muted"),
                html.H3("-", id=id_name, className="card-text text-primary font-weight-bold"),
            ]
        ),
        className="mb-4 shadow-sm border-0",
    )


region_options, default_region = _region_options()


layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(html.H2("Tourism Recovery Dashboard", className="mb-4"), width=8),
                dbc.Col(
                    dcc.Dropdown(
                        id="region-filter",
                        options=region_options,
                        value=default_region,
                        clearable=False,
                        className="mb-4",
                    ),
                    width=4,
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(create_kpi_card("Total Visitors (YTD)", "kpi-total-visitors"), width=4),
                dbc.Col(create_kpi_card("Year-over-Year Growth", "kpi-yoy-growth"), width=4),
                dbc.Col(create_kpi_card("Recovery Rate (vs Pre-Pandemic)", "kpi-recovery-rate"), width=4),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5("Monthly Visitor Trend", className="card-title"),
                                dcc.Graph(id="visitor-trend-chart"),
                            ]
                        ),
                        className="shadow-sm border-0",
                    ),
                    width=12,
                )
            ]
        ),
    ]
)


@callback(
    [
        Output("kpi-total-visitors", "children"),
        Output("kpi-yoy-growth", "children"),
        Output("kpi-recovery-rate", "children"),
        Output("visitor-trend-chart", "figure"),
    ],
    [Input("region-filter", "value")],
)
def update_dashboard(selected_region: str):
    try:
        summary = get_dashboard_summary(selected_region)
        points = summary.get("monthly_points", [])
        chart_df = pd.DataFrame(points)
        if not chart_df.empty:
            chart_df["date"] = pd.to_datetime(chart_df["date"])
        total_visitors = summary.get("total_visitors", 0)
        yoy_growth = summary.get("yoy_growth_pct")
        recovery_rate = summary.get("recovery_rate_pct")

        formatted_total = f"{int(total_visitors):,}"
        formatted_yoy = "N/A" if yoy_growth is None else f"{yoy_growth:.1f}%"
        formatted_recovery = "N/A" if recovery_rate is None else f"{recovery_rate:.1f}%"

        fig = px.line(
            chart_df,
            x="date",
            y="visitors",
            markers=True,
            color_discrete_sequence=["#2C3E50"],
        )
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis_title=None,
            yaxis_title="Visitors",
        )
        return formatted_total, formatted_yoy, formatted_recovery, fig

    except ApiUnavailableError:
        filtered_df = mock_data[mock_data["Region"] == selected_region]
        total_visitors = filtered_df["Visitors"].sum()
        fig = px.line(
            filtered_df,
            x="Date",
            y="Visitors",
            markers=True,
            color_discrete_sequence=["#2C3E50"],
        )
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis_title=None,
        )
        return f"{total_visitors:,}", "N/A", "N/A", fig