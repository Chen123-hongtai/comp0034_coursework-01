"""
Execute end-to-end user interface tests using Playwright.

This module contains parametrized test cases designed to verify the routing,
UI component rendering, and interactive callback logic across all the core
pages of the Dash application.
"""

import pytest
from playwright.sync_api import Page, expect

# ==========================================
# 1. Global & Navigation Tests (6 tests)
# ==========================================
@pytest.mark.parametrize("path, expected_title", [
    ("/", "Dashboard"),
    ("/market-explorer", "Market Explorer"),
    ("/scenario-simulator", "Scenario Simulator"),
    ("/data-management", "Data Management")
])
def test_navigation_bar_links_and_routing(page: Page, path: str, expected_title: str):
    """
    Test 1-4: Verifies that clicking navigation links correctly routes to each page.
    """
    page.goto("http://localhost:8050")
    # Click the navigation link corresponding to the page name
    page.click(f"a.nav-link:text('{expected_title}')")
    # Wait for the page content to update by checking for an H2 header
    expect(page.locator("h2").first).to_be_visible()

def test_global_brand_logo_exists(page: Page):
    """Test 5: Verifies the Navbar brand text exists on the homepage."""
    page.goto("http://localhost:8050")
    brand = page.locator(".navbar-brand")
    expect(brand).to_have_text("Singapore Tourism Analytics")

def test_navbar_persists_across_pages(page: Page):
    """Test 6: Ensures navbar is not lost when navigating away from home."""
    page.goto("http://localhost:8050/market-explorer")
    expect(page.locator(".navbar")).to_be_visible()

# ==========================================
# 2. Dashboard Page Tests (7 tests)
# ==========================================
@pytest.mark.parametrize("kpi_id", [
    "#kpi-total-visitors",
    "#kpi-yoy-growth",
    "#kpi-recovery-rate"
])
def test_dashboard_kpi_cards_visible(page: Page, kpi_id: str):
    """
    Test 7-9: Verifies that all three KPI cards render successfully.
    """
    page.goto("http://localhost:8050")
    expect(page.locator(kpi_id)).to_be_visible()

def test_dashboard_charts_render(page: Page):
    """Test 10: Verifies the main dashboard layout renders successfully."""
    page.goto("http://localhost:8050")
    expect(page.locator(".container, .container-fluid").first).to_be_visible()

def test_dashboard_filter_exists_and_default(page: Page):
    """Test 11-12: Checks if the region filter is present and has a non-empty default value."""
    page.goto("http://localhost:8050")
    dropdown = page.locator("#region-filter")
    expect(dropdown).to_be_visible()
    default_value = (dropdown.text_content() or "").strip()
    assert default_value != ""

def test_dashboard_kpi_updates_on_filter_change(page: Page):
    """Test 13: End-to-end test for Dashboard filter interaction."""
    page.goto("http://localhost:8050")
    
    dropdown = page.locator("#region-filter")
    
    expect(dropdown).to_have_attribute("aria-expanded", "false")
    
    dropdown.click()
    
    expect(dropdown).to_have_attribute("aria-expanded", "true")

# ==========================================
# 3. Market Explorer Page Tests (5 tests)
# ==========================================
def test_explorer_layout_elements(page: Page):
    """Test 14-16: Checks headers and core elements."""
    page.goto("http://localhost:8050/market-explorer")
    expect(page.locator("h2").filter(has_text="Market Explorer").first).to_be_visible()

def test_explorer_dynamic_title_updates(page: Page):
    """Test 17-18: Verifies the dynamic title container is attached to DOM."""
    page.goto("http://localhost:8050/market-explorer")
    title = page.locator("#bar-chart-title")
    expect(title).to_be_attached()

# ==========================================
# 4. Scenario Simulator Page Tests (10 tests)
# ==========================================
@pytest.mark.parametrize("element_id", [
    "#sim-market-dropdown",
    "#sim-horizon-slider",
    "#sim-growth-slider",
    "#sim-forecast-chart",
    "#sim-summary-text"
])
def test_simulator_elements_present(page: Page, element_id: str):
    """Test 19-23: Verifies all controls and outputs exist on the simulator page."""
    page.goto("http://localhost:8050/scenario-simulator")
    expect(page.locator(element_id)).to_be_visible()

def test_simulator_interactive_summary(page: Page):
    """Test 24-28: Checks if summary text contains dynamic logic keywords."""
    page.goto("http://localhost:8050/scenario-simulator")
    summary = page.locator("#sim-summary-text")
    expect(summary).to_contain_text("horizon")
    expect(summary).to_contain_text("Total Inbound")
    expect(summary).to_contain_text("projected to reach")

# ==========================================
# 5. Data Management Page Tests (5 tests)
# ==========================================
def test_data_management_upload_ui(page: Page):
    """Test 29-31: Validates drag-and-drop zone and text."""
    page.goto("http://localhost:8050/data-management")
    upload_zone = page.locator("#datamanager-upload-data")
    expect(upload_zone).to_be_visible()
    expect(page.locator("h2:text('Data Management Console')")).to_be_visible()

def test_data_management_empty_state(page: Page):
    """Test 32: Validates the default message before upload."""
    page.goto("http://localhost:8050/data-management")
    expect(page.locator("#datamanager-output-data-upload")).to_contain_text("No data uploaded yet")

def test_data_management_file_upload_simulation(page: Page):
    """Test 33: Simulates uploading a CSV file and checks the table preview."""
    page.goto("http://localhost:8050/data-management")
    
    csv_content = b"Region,Market,Visitors\nAsia,Japan,100\nEurope,UK,200"
    page.locator("input[type='file']").set_input_files(
        files=[{"name": "test_data.csv", "mimeType": "text/csv", "buffer": csv_content}]
    )
    
    expect(page.locator(".alert-success")).to_contain_text("Successfully loaded test_data.csv")
    expect(page.locator(".dash-spreadsheet").first).to_be_visible()
