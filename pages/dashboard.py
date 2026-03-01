"""
Render the main dashboard page for tourism analytics.

This module provides a high-level overview of inbound tourism performance.
It includes key performance indicator (KPI) cards and a visitor trend chart,
all of which update dynamically based on the selected geographic region.
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

# Register this page with the Dash app.
# path='/' makes this the home page of the application.
dash.register_page(__name__, path='/', name='Dashboard')

# ==========================================
# Mock Data (To be replaced by your Services layer)
# ==========================================
# Creating some dummy data to ensure the charts render correctly for testing.
dates = pd.date_range(start="2023-01-01", periods=12, freq="ME")
mock_data = pd.DataFrame({
    "Date": dates.tolist() * 2,
    "Visitors": [100, 120, 150, 130, 160, 180, 200, 210, 190, 220, 240, 250] + 
                [80, 90, 110, 100, 120, 140, 150, 160, 140, 170, 190, 200],
    "Region": ["Southeast Asia"] * 12 + ["Europe"] * 12
})

# ==========================================
# Helper Functions for UI Components
# ==========================================
def create_kpi_card(title: str, id_name: str) -> dbc.Card:
    """
    Create a standardized Key Performance Indicator (KPI) card component.
    """
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-title text-muted"),
            html.H3("-", id=id_name, className="card-text text-primary font-weight-bold")
        ]),
        className="mb-4 shadow-sm border-0"
    )

# ==========================================
# Page Layout
# ==========================================
layout = html.Div([
    # Row 1: Page Title and Global Filters
    dbc.Row([
        dbc.Col(html.H2("Tourism Recovery Dashboard", className="mb-4"), width=8),
        dbc.Col(
            # Dropdown filter for Region selection
            dcc.Dropdown(
                id='region-filter',
                options=[{'label': region, 'value': region} for region in mock_data['Region'].unique()],
                value='Southeast Asia', # Default value
                clearable=False,
                className="mb-4"
            ),
            width=4
        )
    ]),

    # Row 2: KPI Cards
    dbc.Row([
        dbc.Col(create_kpi_card("Total Visitors (YTD)", "kpi-total-visitors"), width=4),
        dbc.Col(create_kpi_card("Year-over-Year Growth", "kpi-yoy-growth"), width=4),
        dbc.Col(create_kpi_card("Recovery Rate (vs Pre-Pandemic)", "kpi-recovery-rate"), width=4),
    ]),

    # Row 3: Main Charts
    dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H5("Monthly Visitor Trend", className="card-title"),
                    # The Graph component where Plotly figures are rendered
                    dcc.Graph(id='visitor-trend-chart')
                ]),
                className="shadow-sm border-0"
            ),
            width=12 # Takes up the full width
        )
    ])
])

# ==========================================
# Callbacks (Interactivity / Logic)
# ==========================================
@callback(
    # Outputs: Which components to update based on the input
    [Output('kpi-total-visitors', 'children'),
     Output('visitor-trend-chart', 'figure')],
    # Inputs: Which user action triggers this function
    [Input('region-filter', 'value')]
)
def update_dashboard(selected_region):
    """
    Updates the KPI cards and charts whenever the user changes the region filter.
    """
    # 1. Filter the data based on user selection
    filtered_df = mock_data[mock_data['Region'] == selected_region]
    
    # 2. Calculate KPI values (Mock calculations for now)
    total_visitors = filtered_df['Visitors'].sum()
    formatted_total = f"{total_visitors:,}" # Format with commas
    
    # 3. Build the Plotly figure for the trend chart
    fig = px.line(
        filtered_df, 
        x='Date', 
        y='Visitors',
        markers=True,
        color_discrete_sequence=['#2C3E50'] # Matching the FLATLY theme
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_title=None
    )
    
    # 4. Return the calculated values to the Output components
    return formatted_total, fig