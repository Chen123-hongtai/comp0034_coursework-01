"""
Display hierarchical market data using interactive visualisations.

This module allows users to explore tourism data across different regions
and specific markets. It utilises a Plotly treemap for volume and growth
visualisation, alongside a bar chart for detailed regional comparisons.
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

# Register this page with the Dash app.
dash.register_page(__name__, name='Market Explorer')

# ==========================================
# Mock Hierarchical Data
# To be replaced by SeriesMaster and Observation joins from your database
# ==========================================
mock_market_data = pd.DataFrame({
    'Region': ['Southeast Asia', 'Southeast Asia', 'Southeast Asia', 'Europe', 'Europe', 'North America', 'North America'],
    'Market': ['Indonesia', 'Malaysia', 'Thailand', 'United Kingdom', 'Germany', 'USA', 'Canada'],
    'Visitors_YTD': [250000, 180000, 150000, 120000, 95000, 150000, 65000],
    'YoY_Growth_Pct': [15.2, 12.0, 18.5, 5.4, 2.1, 8.9, 4.5]
})
# Add a static root column for the treemap hierarchy
mock_market_data['Global'] = 'Total Inbound' 

# ==========================================
# Page Layout
# ==========================================
layout = html.Div([
    # Row 1: Page Header and Description
    dbc.Row([
        dbc.Col([
            html.H2("Market Explorer", className="mb-2"),
            html.P(
                "Analyze hierarchical market performance. Use the Treemap to visualize volume "
                "and growth across regions, and the Bar Chart for detailed market comparisons.",
                className="text-muted mb-4"
            )
        ], width=12)
    ]),

    # Row 2: Controls (Filters)
    dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.Label("Select Region for Detail View:", className="font-weight-bold"),
                    dcc.Dropdown(
                        id='explorer-region-dropdown',
                        # Extract unique regions from the mock data
                        options=[{'label': r, 'value': r} for r in mock_market_data['Region'].unique()],
                        value='Southeast Asia', # Default selection
                        clearable=False
                    )
                ]),
                className="mb-4 shadow-sm border-0"
            ),
            width=4
        )
    ]),

    # Row 3: Visualizations (Treemap and Bar Chart side-by-side)
    dbc.Row([
        # Left Column: Treemap (Hierarchical View)
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H5("Global Market Share & Growth", className="card-title"),
                    dcc.Graph(id='market-treemap-chart')
                ]),
                className="shadow-sm border-0 h-100"
            ),
            width=7 # Takes 7/12 of the screen width
        ),
        
        # Right Column: Bar Chart (Detailed comparison within a region)
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H5(id='bar-chart-title', className="card-title"),
                    dcc.Graph(id='market-bar-chart')
                ]),
                className="shadow-sm border-0 h-100"
            ),
            width=5 # Takes 5/12 of the screen width
        )
    ], className="mb-4") # Added margin-bottom for better spacing
])

# ==========================================
# Callbacks (Interactivity / Logic)
# ==========================================
@callback(
    [Output('market-treemap-chart', 'figure'),
     Output('market-bar-chart', 'figure'),
     Output('bar-chart-title', 'children')],
    [Input('explorer-region-dropdown', 'value')]
)
def update_explorer_charts(selected_region):
    """
    Updates the Treemap and Bar Chart based on the selected region.
    """
    
    # 1. Build the Treemap Figure (Shows the entire globe, not filtered by dropdown)
    # Size represents Visitors, Color represents Year-over-Year Growth
    fig_tree = px.treemap(
        mock_market_data,
        path=['Global', 'Region', 'Market'],
        values='Visitors_YTD',
        color='YoY_Growth_Pct',
        color_continuous_scale='RdBu', # Red for negative/low, Blue for positive/high growth
        color_continuous_midpoint=0    # 0% growth is the midpoint color
    )
    fig_tree.update_layout(margin=dict(t=10, l=10, r=10, b=10))

    # 2. Filter data for the Bar Chart (Shows specific markets in the selected region)
    region_data = mock_market_data[mock_market_data['Region'] == selected_region]
    
    # Sort data to show highest growth first
    region_data = region_data.sort_values(by='YoY_Growth_Pct', ascending=True)

    # 3. Build the Bar Chart Figure
    fig_bar = px.bar(
        region_data,
        x='YoY_Growth_Pct',
        y='Market',
        orientation='h', # Horizontal bar chart for better readability of market names
        text='YoY_Growth_Pct',
        color='YoY_Growth_Pct',
        color_continuous_scale='RdBu',
        color_continuous_midpoint=0
    )
    # Format text on bars to show percentage
    fig_bar.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig_bar.update_layout(
        margin=dict(t=10, l=10, r=10, b=10),
        coloraxis_showscale=False, # Hide the colorbar for the bar chart to save space
        xaxis_title="YoY Growth (%)",
        yaxis_title=None
    )

    # 4. Generate dynamic title for the Bar Chart
    bar_title = f"Market Performance: {selected_region}"

    return fig_tree, fig_bar, bar_title