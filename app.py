"""
Initialize and run the Singapore Tourism Analytics Dash application.

This module configures the main Dash application instance, sets up the
multi-page routing capability, defines the global navigation bar, and
serves as the entry point for running the development server.
"""

import dash
from dash import html
import dash_bootstrap_components as dbc

# Initialize the Dash application.
# `use_pages=True` enables the native multi-page routing mechanism.
# `external_stylesheets` applies a Bootstrap theme (FLATLY is clean and professional).
# suppress_callback_exceptions=True prevents errors when components are generated dynamically across pages.
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True 
)

# Define the global navigation bar.
# This component will remain visible at the top of every page.
navbar = dbc.NavbarSimple(
    children=[
        # Dynamically generate navigation links based on the registered pages in the `pages/` directory.
        dbc.NavItem(dbc.NavLink(page['name'], href=page['relative_path']))
        for page in dash.page_registry.values()
    ],
    brand="Singapore Tourism Analytics",
    brand_href="/",
    color="primary",
    dark=True,
    className="mb-4" # Adds margin to the bottom of the navbar
)

# Define the global layout of the application.
app.layout = html.Div([
    # 1. Render the global navigation bar
    navbar,
    
    # 2. Render the specific content of the current active page.
    # dbc.Container(fluid=True) allows the content to utilize the full width of the screen.
    dbc.Container(
        dash.page_container, 
        fluid=True 
    )
])

# Entry point for running the development server.
if __name__ == '__main__':
    # debug=True enables hot-reloading and helpful error messages in the browser.
    app.run(debug=True)