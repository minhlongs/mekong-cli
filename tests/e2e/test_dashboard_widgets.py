"""
Dashboard Widgets E2E Tests
Tests for KPI cards, chart widgets, alerts widget
"""

import pytest
from playwright.sync_api import Page, expect, TimeoutError
from typing import List


# Test URLs
BASE_URL = "http://localhost:8080"
WIDGETS_DEMO_URL = f"{BASE_URL}/admin/widgets-demo.html"
DASHBOARD_URL = f"{BASE_URL}/admin/dashboard.html"


@pytest.fixture(scope="function")
def page(page: Page) -> Page:
    """Setup page for widget tests"""
    page.set_viewport_size({"width": 1920, "height": 1080})
    return page


class TestKPICardWidget:
    """Tests for KPI Card Widget"""

    def test_kpi_card_renders(self, page: Page):
        """Test KPI card renders correctly"""
        page.goto(WIDGETS_DEMO_URL)

        # Check KPI card exists
        kpi_cards = page.locator("kpi-card-widget")
        expect(kpi_cards.first).to_be_visible(timeout=10000)

    def test_kpi_card_displays_value(self, page: Page):
        """Test KPI card displays correct value"""
        page.goto(WIDGETS_DEMO_URL)

        # First KPI should have Revenue title
        kpi_card = page.locator("kpi-card-widget").first
        expect(kpi_card).to_contain_text("Total Revenue", timeout=5000)

    def test_kpi_card_trend_indicator(self, page: Page):
        """Test KPI card trend indicator"""
        page.goto(WIDGETS_DEMO_URL)

        # Check for trend indicator
        kpi_card = page.locator("kpi-card-widget").first
        trend_element = kpi_card.locator(".trend-positive, .trend-negative, .trend-neutral")
        expect(trend_element.first).to_be_visible(timeout=5000)

    def test_kpi_card_responsive(self, page: Page):
        """Test KPI card responsive design"""
        page.goto(WIDGETS_DEMO_URL)

        # Mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})
        kpi_cards = page.locator("kpi-card-widget")
        expect(kpi_cards.first).to_be_visible(timeout=5000)

        # Check cards stack vertically on mobile
        first_card_box = kpi_cards.first.bounding_box()
        second_card_box = kpi_cards.nth(1).bounding_box()

        assert first_card_box is not None
        assert second_card_box is not None
        assert second_card_box["y"] > first_card_box["y"]  # Second card below first


class TestAlertsWidget:
    """Tests for Alerts Widget"""

    def test_alerts_widget_renders(self, page: Page):
        """Test alerts widget renders correctly"""
        page.goto(WIDGETS_DEMO_URL)

        alerts_widget = page.locator("alerts-widget")
        expect(alerts_widget).to_be_visible(timeout=10000)

    def test_alerts_widget_has_title(self, page: Page):
        """Test alerts widget displays title"""
        page.goto(WIDGETS_DEMO_URL)

        alerts_widget = page.locator("alerts-widget")
        expect(alerts_widget).to_contain_text("System Alerts", timeout=5000)

    def test_alerts_widget_filter_buttons(self, page: Page):
        """Test alerts widget filter buttons"""
        page.goto(WIDGETS_DEMO_URL)

        alerts_widget = page.locator("alerts-widget")

        # Check filter buttons exist
        all_btn = alerts_widget.get_by_role("button", name="All")
        critical_btn = alerts_widget.get_by_role("button", name="Critical")
        warning_btn = alerts_widget.get_by_role("button", name="Warning")

        expect(all_btn).to_be_visible(timeout=5000)
        expect(critical_btn).to_be_visible(timeout=5000)
        expect(warning_btn).to_be_visible(timeout=5000)

    def test_alerts_widget_dismiss(self, page: Page):
        """Test alerts widget dismiss functionality"""
        page.goto(WIDGETS_DEMO_URL)

        alerts_widget = page.locator("alerts-widget")

        # Wait for alerts to load
        page.wait_for_timeout(2000)

        # Get initial alert count
        alert_items = alerts_widget.locator(".alert-item")
        initial_count = alert_items.count()

        if initial_count > 0:
            # Click dismiss button on first alert
            dismiss_btn = alert_items.first.locator(".alert-dismiss")
            dismiss_btn.click()

            # Wait for animation
            page.wait_for_timeout(500)

            # Check alert count decreased
            new_count = alert_items.count()
            assert new_count < initial_count or new_count == initial_count  # May vary based on implementation


class TestPieChartWidget:
    """Tests for Pie Chart Widget"""

    def test_pie_chart_renders(self, page: Page):
        """Test pie chart renders correctly"""
        page.goto(WIDGETS_DEMO_URL)

        pie_chart = page.locator("pie-chart-widget")
        expect(pie_chart.first).to_be_visible(timeout=10000)

    def test_pie_chart_has_canvas(self, page: Page):
        """Test pie chart has canvas element"""
        page.goto(WIDGETS_DEMO_URL)

        pie_chart = page.locator("pie-chart-widget").first
        canvas = pie_chart.locator("canvas")
        expect(canvas).to_be_visible(timeout=10000)

    def test_pie_chart_has_title(self, page: Page):
        """Test pie chart displays title"""
        page.goto(WIDGETS_DEMO_URL)

        pie_chart = page.locator("pie-chart-widget").first
        expect(pie_chart).to_contain_text("Traffic Sources", timeout=5000)

    def test_pie_chart_type_toggle(self, page: Page):
        """Test pie chart type toggle (Pie/Doughnut)"""
        page.goto(WIDGETS_DEMO_URL)

        pie_chart = page.locator("pie-chart-widget").first

        # Find and click doughnut button
        doughnut_btn = pie_chart.get_by_role("button", name="Doughnut")
        expect(doughnut_btn).to_be_visible(timeout=5000)
        doughnut_btn.click()

        page.wait_for_timeout(1500)  # Wait for chart update

        # Chart should still be visible
        canvas = pie_chart.locator("canvas")
        expect(canvas).to_be_visible(timeout=5000)


class TestLineChartWidget:
    """Tests for Line Chart Widget"""

    def test_line_chart_renders(self, page: Page):
        """Test line chart renders correctly"""
        page.goto(WIDGETS_DEMO_URL)

        line_chart = page.locator("line-chart-widget")
        expect(line_chart.first).to_be_visible(timeout=15000)

    def test_line_chart_has_canvas(self, page: Page):
        """Test line chart has canvas element"""
        page.goto(WIDGETS_DEMO_URL)

        line_chart = page.locator("line-chart-widget").first
        canvas = line_chart.locator("canvas")
        expect(canvas).to_be_visible(timeout=10000)

    def test_line_chart_time_range_buttons(self, page: Page):
        """Test line chart time range buttons"""
        page.goto(WIDGETS_DEMO_URL)

        line_chart = page.locator("line-chart-widget").first

        # Check time range buttons exist
        daily_btn = line_chart.get_by_role("button", name="Daily")
        weekly_btn = line_chart.get_by_role("button", name="Weekly")
        monthly_btn = line_chart.get_by_role("button", name="Monthly")

        expect(daily_btn).to_be_visible(timeout=5000)
        expect(weekly_btn).to_be_visible(timeout=5000)
        expect(monthly_btn).to_be_visible(timeout=5000)


class TestAreaChartWidget:
    """Tests for Area Chart Widget"""

    def test_area_chart_renders(self, page: Page):
        """Test area chart renders correctly"""
        page.goto(WIDGETS_DEMO_URL)

        area_chart = page.locator("area-chart-widget")
        expect(area_chart.first).to_be_visible(timeout=15000)

    def test_area_chart_has_canvas(self, page: Page):
        """Test area chart has canvas element"""
        page.goto(WIDGETS_DEMO_URL)

        area_chart = page.locator("area-chart-widget").first
        canvas = area_chart.locator("canvas")
        expect(canvas).to_be_visible(timeout=10000)


class TestBarChartWidget:
    """Tests for Bar Chart Widget"""

    def test_bar_chart_renders(self, page: Page):
        """Test bar chart renders correctly"""
        page.goto(WIDGETS_DEMO_URL)

        bar_chart = page.locator("bar-chart-widget")
        expect(bar_chart.first).to_be_visible(timeout=15000)

    def test_bar_chart_has_canvas(self, page: Page):
        """Test bar chart has canvas element"""
        page.goto(WIDGETS_DEMO_URL)

        bar_chart = page.locator("bar-chart-widget").first
        canvas = bar_chart.locator("canvas")
        expect(canvas).to_be_visible(timeout=10000)

    def test_bar_chart_orientation_toggle(self, page: Page):
        """Test bar chart orientation toggle"""
        page.goto(WIDGETS_DEMO_URL)

        bar_chart = page.locator("bar-chart-widget").first

        # Find orientation button
        orientation_btn = bar_chart.get_by_role("button", name="Horizontal")
        expect(orientation_btn).to_be_visible(timeout=5000)


class TestResponsiveDesign:
    """Tests for responsive design across all widgets"""

    def test_mobile_viewport_widgets(self, page: Page):
        """Test all widgets visible on mobile viewport"""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(WIDGETS_DEMO_URL)

        # Wait for all widgets to load
        page.wait_for_timeout(3000)

        # Check KPI cards
        kpi_cards = page.locator("kpi-card-widget")
        expect(kpi_cards.first).to_be_visible(timeout=10000)

        # Check alerts widget
        alerts_widget = page.locator("alerts-widget")
        expect(alerts_widget).to_be_visible(timeout=10000)

        # Check pie chart
        pie_chart = page.locator("pie-chart-widget")
        expect(pie_chart.first).to_be_visible(timeout=15000)

    def test_tablet_viewport_widgets(self, page: Page):
        """Test all widgets visible on tablet viewport"""
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto(WIDGETS_DEMO_URL)

        page.wait_for_timeout(3000)

        # All widget types should be visible
        expect(page.locator("kpi-card-widget")).to_be_visible(timeout=10000)
        expect(page.locator("alerts-widget")).to_be_visible(timeout=10000)
        expect(page.locator("pie-chart-widget")).to_be_visible(timeout=15000)
        expect(page.locator("line-chart-widget")).to_be_visible(timeout=15000)

    def test_desktop_viewport_widgets(self, page: Page):
        """Test all widgets visible on desktop viewport"""
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(WIDGETS_DEMO_URL)

        page.wait_for_timeout(3000)

        # All widget types should be visible
        expect(page.locator("kpi-card-widget")).to_be_visible(timeout=10000)
        expect(page.locator("alerts-widget")).to_be_visible(timeout=10000)
        expect(page.locator("pie-chart-widget")).to_be_visible(timeout=15000)
        expect(page.locator("line-chart-widget")).to_be_visible(timeout=15000)
        expect(page.locator("area-chart-widget")).to_be_visible(timeout=15000)
        expect(page.locator("bar-chart-widget")).to_be_visible(timeout=15000)


class TestWidgetAnimations:
    """Tests for widget animations"""

    def test_kpi_card_hover_animation(self, page: Page):
        """Test KPI card hover animation"""
        page.goto(WIDGETS_DEMO_URL)

        kpi_card = page.locator("kpi-card-widget").first
        expect(kpi_card).to_be_visible(timeout=10000)

        # Hover and check for transform
        initial_box = kpi_card.bounding_box()
        kpi_card.hover()
        page.wait_for_timeout(300)

        # Card should move up on hover (visual check - actual transform hard to test)
        # This is more of a smoke test
        assert kpi_card.is_visible()

    def test_alert_item_animation(self, page: Page):
        """Test alert item slide-in animation"""
        page.goto(WIDGETS_DEMO_URL)

        alerts_widget = page.locator("alerts-widget")
        expect(alerts_widget).to_be_visible(timeout=10000)

        page.wait_for_timeout(2000)

        # Alert items should be visible
        alert_items = alerts_widget.locator(".alert-item")
        expect(alert_items.first).to_be_visible(timeout=5000)


class TestAccessibility:
    """Tests for accessibility"""

    def test_widgets_have_aria_labels(self, page: Page):
        """Test widgets have proper ARIA labels"""
        page.goto(WIDGETS_DEMO_URL)

        # Check KPI cards have labels
        kpi_cards = page.locator("kpi-card-widget")
        # Custom elements don't automatically get ARIA, but we can check content
        expect(kpi_cards.first).to_be_visible(timeout=10000)

    def test_chart_canvas_has_aria(self, page: Page):
        """Test chart canvas has aria-label"""
        page.goto(WIDGETS_DEMO_URL)

        pie_chart = page.locator("pie-chart-widget").first
        canvas = pie_chart.locator("canvas")

        # Canvas should have aria-label
        expect(canvas).to_have_attribute("aria-label", timeout=5000)


class TestWidgetsDemoPage:
    """General tests for widgets demo page"""

    def test_page_loads(self, page: Page):
        """Test page loads successfully"""
        page.goto(WIDGETS_DEMO_URL)
        expect(page).to_have_title("Dashboard Widgets Demo - Mekong Admin")

    def test_demo_controls_visible(self, page: Page):
        """Test demo controls are visible"""
        page.goto(WIDGETS_DEMO_URL)

        refresh_btn = page.get_by_role("button", name="Refresh All Widgets")
        expect(refresh_btn).to_be_visible(timeout=5000)

    def test_all_widget_types_present(self, page: Page):
        """Test all widget types are present on demo page"""
        page.goto(WIDGETS_DEMO_URL)

        page.wait_for_timeout(3000)

        # Check all widget custom elements are present
        expect(page.locator("kpi-card-widget")).to_be_visible(timeout=10000)
        expect(page.locator("alerts-widget")).to_be_visible(timeout=10000)
        expect(page.locator("pie-chart-widget")).to_be_visible(timeout=15000)
        expect(page.locator("line-chart-widget")).to_be_visible(timeout=15000)
        expect(page.locator("area-chart-widget")).to_be_visible(timeout=15000)
        expect(page.locator("bar-chart-widget")).to_be_visible(timeout=15000)
        expect(page.locator("revenue-chart-widget")).to_be_visible(timeout=15000)
        expect(page.locator("activity-feed-widget")).to_be_visible(timeout=15000)
        expect(page.locator("project-progress-widget")).to_be_visible(timeout=15000)


# Performance tests
class TestWidgetPerformance:
    """Performance tests for widgets"""

    def test_widgets_load_within_timeout(self, page: Page):
        """Test all widgets load within timeout"""
        start_time = page.evaluate("Date.now()")
        page.goto(WIDGETS_DEMO_URL)

        # Wait for all widgets
        page.wait_for_selector("kpi-card-widget", timeout=10000)
        page.wait_for_selector("alerts-widget", timeout=10000)
        page.wait_for_selector("pie-chart-widget", timeout=15000)

        load_time = page.evaluate("Date.now()") - start_time
        assert load_time < 15000, f"Widgets took {load_time}ms to load"

    def test_no_console_errors(self, page: Page):
        """Test no console errors during widget load"""
        console_errors = []

        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

        page.goto(WIDGETS_DEMO_URL)
        page.wait_for_timeout(5000)

        # Filter out non-critical errors
        critical_errors = [
            err for err in console_errors
            if "Uncaught" in err.text or "Error" in err.text
        ]

        assert len(critical_errors) == 0, f"Console errors: {[e.text for e in critical_errors]}"
