"""Display hierarchical market data using interactive visualisations."""

from __future__ import annotations

import dash
from dash import Input, Output, callback, dcc, html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

from services.api_client import ApiUnavailableError, get_market_explorer_metrics


dash.register_page(__name__, name="Market Explorer")


mock_market_data = pd.DataFrame(
    {
        "Region": [
            "Southeast Asia",
            "Southeast Asia",
            "Southeast Asia",
            "Europe",
            "Europe",
            "North America",
            "North America",
        ],
        "Market": ["Indonesia", "Malaysia", "Thailand", "United Kingdom", "Germany", "USA", "Canada"],
        "Visitors_YTD": [250000, 180000, 150000, 120000, 95000, 150000, 65000],
        "YoY_Growth_Pct": [15.2, 12.0, 18.5, 5.4, 2.1, 8.9, 4.5],
    }
)
mock_market_data["Global"] = "Total Inbound"


def _load_market_data() -> pd.DataFrame:
    try:
        data = get_market_explorer_metrics()
        df = pd.DataFrame(data)
        if df.empty:
            raise ApiUnavailableError("Empty response from API")
        df = df.rename(
            columns={
                "region": "Region",
                "market": "Market",
                "visitors_ytd": "Visitors_YTD",
                "yoy_growth_pct": "YoY_Growth_Pct",
            }
        )
        df["YoY_Growth_Pct"] = df["YoY_Growth_Pct"].fillna(0.0)
        df["Global"] = "Total Inbound"
        return df
    except ApiUnavailableError:
        return mock_market_data.copy()


initial_data = _load_market_data()


layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H2("Market Explorer", className="mb-2"),
                        html.P(
                            "Analyze hierarchical market performance. Use the Treemap to visualize volume "
                            "and growth across regions, and the Bar Chart for detailed market comparisons.",
                            className="text-muted mb-4",
                        ),
                    ],
                    width=12,
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Label("Select Region for Detail View:", className="font-weight-bold"),
                                dcc.Dropdown(
                                    id="explorer-region-dropdown",
                                    options=[{"label": r, "value": r} for r in initial_data["Region"].unique()],
                                    value=initial_data["Region"].iloc[0],
                                    clearable=False,
                                ),
                            ]
                        ),
                        className="mb-4 shadow-sm border-0",
                    ),
                    width=4,
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5("Global Market Share & Growth", className="card-title"),
                                dcc.Graph(id="market-treemap-chart"),
                            ]
                        ),
                        className="shadow-sm border-0 h-100",
                    ),
                    width=7,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([html.H5(id="bar-chart-title", className="card-title"), dcc.Graph(id="market-bar-chart")]),
                        className="shadow-sm border-0 h-100",
                    ),
                    width=5,
                ),
            ],
            className="mb-4",
        ),
    ]
)


@callback(
    [
        Output("market-treemap-chart", "figure"),
        Output("market-bar-chart", "figure"),
        Output("bar-chart-title", "children"),
    ],
    [Input("explorer-region-dropdown", "value")],
)
def update_explorer_charts(selected_region: str):
    dataset = _load_market_data()

    fig_tree = px.treemap(
        dataset,
        path=["Global", "Region", "Market"],
        values="Visitors_YTD",
        color="YoY_Growth_Pct",
        color_continuous_scale="RdBu",
        color_continuous_midpoint=0,
    )
    fig_tree.update_layout(margin=dict(t=10, l=10, r=10, b=10))

    region_data = dataset[dataset["Region"] == selected_region].sort_values(by="YoY_Growth_Pct", ascending=True)

    fig_bar = px.bar(
        region_data,
        x="YoY_Growth_Pct",
        y="Market",
        orientation="h",
        text="YoY_Growth_Pct",
        color="YoY_Growth_Pct",
        color_continuous_scale="RdBu",
        color_continuous_midpoint=0,
    )
    fig_bar.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_bar.update_layout(
        margin=dict(t=10, l=10, r=10, b=10),
        coloraxis_showscale=False,
        xaxis_title="YoY Growth (%)",
        yaxis_title=None,
    )

    return fig_tree, fig_bar, f"Market Performance: {selected_region}"