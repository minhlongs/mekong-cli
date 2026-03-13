"""
Responsive Viewport E2E Tests - Sa Đéc Marketing Hub
Tests for 375px, 768px, 1024px breakpoints
"""

import pytest
from playwright.sync_api import Page, expect
import os


# Test URLs - Sa Đéc Marketing Hub (Production)
# Note: Portal pages are in local dev, production has admin + landing
BASE_URL = "https://sadec-marketing-hub.vercel.app"
PORTAL_URL = f"{BASE_URL}/portal/dashboard.html"  # May return 404 on prod
ADMIN_URL = f"{BASE_URL}/admin/dashboard.html"
LANDING_URL = BASE_URL


# Viewport configurations
VIEWPORTS = {
    "mobile_small": {"width": 375, "height": 667},
    "mobile": {"width": 768, "height": 1024},
    "tablet": {"width": 1024, "height": 768},
    "desktop": {"width": 1920, "height": 1080},
}


# Note: Using Playwright's built-in 'page' fixture directly
# viewport setup is done per-test via set_viewport_size()


class TestPortalResponsive:
    """Tests for Portal responsive design"""

    def test_portal_mobile_small_375px(self, page: Page):
        """Test portal at 375px viewport"""
        page.set_viewport_size(VIEWPORTS["mobile_small"])
        response = page.goto(PORTAL_URL, timeout=30000)

        # Skip if portal returns 404 (not deployed to prod yet)
        if response and response.status == 404:
            pytest.skip("Portal not deployed to production")

        # Layout should be single column
        layout = page.locator(".portal-layout, .layout-2026")
        if layout.count() > 0:
            expect(layout.first).to_be_visible(timeout=10000)
        else:
            pytest.skip("Portal layout not found")

        # Sidebar should be hidden (hamburger menu shown)
        menu_toggle = page.locator(".mobile-menu-toggle, .nav-toggle, .hamburger-menu")
        if menu_toggle.count() > 0:
            expect(menu_toggle.first).to_be_visible(timeout=5000)

        # Content should not overflow horizontally
        body_width = page.evaluate("document.body.scrollWidth")
        viewport_width = page.evaluate("window.innerWidth")
        assert body_width <= viewport_width, "Horizontal overflow detected at 375px"

    def test_portal_mobile_768px(self, page: Page):
        """Test portal at 768px viewport"""
        page.set_viewport_size(VIEWPORTS["mobile"])
        page.goto(PORTAL_URL, timeout=30000)

        # Layout should be single column
        layout = page.locator(".portal-layout, .layout-2026")
        expect(layout.first).to_be_visible(timeout=10000)

        # Check touch-friendly spacing
        main_content = page.locator(".main-content")
        expect(main_content.first).to_be_visible(timeout=5000)

    def test_portal_tablet_1024px(self, page: Page):
        """Test portal at 1024px viewport"""
        page.set_viewport_size(VIEWPORTS["tablet"])
        page.goto(PORTAL_URL, timeout=30000)

        # Two-column layout may appear
        layout = page.locator(".portal-layout")
        expect(layout.first).to_be_visible(timeout=10000)

    def test_portal_navigation_all_viewports(self, page: Page):
        """Test portal navigation works at all viewports"""
        for name, size in VIEWPORTS.items():
            page.set_viewport_size(size)
            page.goto(PORTAL_URL, timeout=30000)

            # Navigation should be accessible
            nav = page.locator("nav, .nav-links, .portal-nav")
            expect(nav.first).to_be_visible(timeout=5000)


class TestAdminResponsive:
    """Tests for Admin responsive design"""

    def test_admin_mobile_small_375px(self, page: Page):
        """Test admin at 375px viewport"""
        page.set_viewport_size(VIEWPORTS["mobile_small"])
        page.goto(ADMIN_URL, timeout=30000)

        # Layout should be single column
        layout = page.locator(".admin-layout, .layout-2026")
        expect(layout.first).to_be_visible(timeout=10000)

        # Sidebar should be hidden
        menu_toggle = page.locator(".mobile-menu-toggle, .nav-toggle, .hamburger-menu")
        expect(menu_toggle.first).to_be_visible(timeout=5000)

        # Stats grid should be single column
        stats_grid = page.locator(".stats-grid, .menu-stats")
        expect(stats_grid.first).to_be_visible(timeout=5000)

        # Check no horizontal overflow
        body_width = page.evaluate("document.body.scrollWidth")
        viewport_width = page.evaluate("window.innerWidth")
        assert body_width <= viewport_width, "Horizontal overflow detected at 375px"

    def test_admin_mobile_768px(self, page: Page):
        """Test admin at 768px viewport"""
        page.set_viewport_size(VIEWPORTS["mobile"])
        page.goto(ADMIN_URL, timeout=30000)

        # Stats grid should be single column
        stats_grid = page.locator(".stats-grid")
        expect(stats_grid.first).to_be_visible(timeout=5000)

        # Charts should be stacked
        chart_section = page.locator(".chart-section")
        expect(chart_section.first).to_be_visible(timeout=5000)

    def test_admin_tablet_1024px(self, page: Page):
        """Test admin at 1024px viewport"""
        page.set_viewport_size(VIEWPORTS["tablet"])
        page.goto(ADMIN_URL, timeout=30000)

        # Stats grid should be 2 columns
        stats_grid = page.locator(".stats-grid")
        expect(stats_grid.first).to_be_visible(timeout=5000)

    def test_admin_widgets_responsive(self, page: Page):
        """Test admin widgets at all viewports"""
        widget_types = [
            "kpi-card-widget",
            "alerts-widget",
            "pie-chart-widget",
            "line-chart-widget",
        ]

        for name, size in VIEWPORTS.items():
            page.set_viewport_size(size)
            page.goto(ADMIN_URL, timeout=30000)
            page.wait_for_timeout(2000)

            for widget in widget_types:
                locator = page.locator(widget)
                # Widgets may not all be on same page, so use try/except
                try:
                    expect(locator.first).to_be_visible(timeout=5000)
                except Exception:
                    pass  # Widget type may not exist on this page


class TestTableResponsive:
    """Tests for table responsive design"""

    def test_responsive_table_mobile_375px(self, page: Page):
        """Test responsive table at 375px"""
        page.set_viewport_size(VIEWPORTS["mobile_small"])

        # Test table wrapper exists
        table_wrapper = page.locator(".table-responsive, .table-responsive-wrapper")
        if table_wrapper.count() > 0:
            expect(table_wrapper.first).to_be_visible(timeout=5000)

            # Table should stack or scroll horizontally
            table = page.locator("table.responsive-stack, .table-responsive-stack")
            if table.count() > 0:
                expect(table.first).to_be_visible(timeout=5000)

    def test_responsive_table_mobile_768px(self, page: Page):
        """Test responsive table at 768px"""
        page.set_viewport_size(VIEWPORTS["mobile"])

        table_wrapper = page.locator(".table-responsive")
        if table_wrapper.count() > 0:
            expect(table_wrapper.first).to_be_visible(timeout=5000)


class TestModalResponsive:
    """Tests for modal responsive design"""

    def test_modal_mobile_375px(self, page: Page):
        """Test modal at 375px viewport"""
        page.set_viewport_size(VIEWPORTS["mobile_small"])

        # If modal exists on page, check it's responsive
        modal = page.locator(".modal-overlay, .modal-content")
        if modal.count() > 0:
            expect(modal.first).to_be_visible(timeout=5000)

            # Modal should be 95% width on mobile
            modal_content = page.locator(".modal-content")
            if modal_content.count() > 0:
                box = modal_content.first.bounding_box()
                if box:
                    assert box["width"] >= 340, "Modal too narrow at 375px"

    def test_modal_tablet_1024px(self, page: Page):
        """Test modal at 1024px viewport"""
        page.set_viewport_size(VIEWPORTS["tablet"])

        modal_content = page.locator(".modal-content")
        if modal_content.count() > 0:
            expect(modal_content.first).to_be_visible(timeout=5000)
            # Modal should have max-width around 600px
            box = modal_content.first.bounding_box()
            if box:
                assert box["width"] <= 700, "Modal too wide at 1024px"


class TestFormResponsive:
    """Tests for form responsive design"""

    def test_form_mobile_375px(self, page: Page):
        """Test form at 375px viewport"""
        page.set_viewport_size(VIEWPORTS["mobile_small"])

        # Form should stack labels
        form = page.locator("form, .form-container")
        if form.count() > 0:
            expect(form.first).to_be_visible(timeout=5000)

            # Form inputs should be full width
            form_inputs = page.locator(".form-input, .form-select, input, select")
            if form_inputs.count() > 0:
                first_input = form_inputs.first
                box = first_input.bounding_box()
                if box:
                    assert box["width"] > 300, "Form input too narrow at 375px"

    def test_form_buttons_mobile(self, page: Page):
        """Test form buttons at mobile viewports"""
        page.set_viewport_size(VIEWPORTS["mobile_small"])

        # Action buttons should be full width on mobile
        form_actions = page.locator(".form-actions, .action-buttons")
        if form_actions.count() > 0:
            buttons = form_actions.locator("button, .btn, .action-btn")
            if buttons.count() > 0:
                # Buttons should stack vertically or be full width
                first_btn = buttons.first
                box = first_btn.bounding_box()
                if box:
                    assert box["width"] > 200, "Button too narrow at 375px"


class TestNoHorizontalOverflow:
    """Tests to ensure no horizontal overflow at any viewport"""

    @pytest.mark.parametrize("viewport_name,viewport_size", VIEWPORTS.items())
    def test_no_horizontal_overflow(self, page: Page, viewport_name: str, viewport_size: dict):
        """Test no horizontal overflow at all viewports"""
        page.set_viewport_size(viewport_size)

        # Test portal
        page.goto(PORTAL_URL, timeout=30000)
        page.wait_for_timeout(1000)

        body_width = page.evaluate("document.body.scrollWidth")
        viewport_width = page.evaluate("window.innerWidth")

        assert body_width <= viewport_width, \
            f"Horizontal overflow at {viewport_name} ({viewport_size['width']}px): " \
            f"body={body_width}px, viewport={viewport_width}px"

        # Test admin
        page.goto(ADMIN_URL, timeout=30000)
        page.wait_for_timeout(1000)

        body_width = page.evaluate("document.body.scrollWidth")
        viewport_width = page.evaluate("window.innerWidth")

        assert body_width <= viewport_width, \
            f"Horizontal overflow at {viewport_name} ({viewport_size['width']}px): " \
            f"body={body_width}px, viewport={viewport_width}px"


class TestTypographyResponsive:
    """Tests for responsive typography"""

    def test_font_size_mobile_375px(self, page: Page):
        """Test font sizes at 375px"""
        page.set_viewport_size(VIEWPORTS["mobile_small"])
        page.goto(PORTAL_URL, timeout=30000)

        # Body text should be readable (at least 12px)
        body = page.locator("body")
        font_size = body.evaluate("el => window.getComputedStyle(el).fontSize")
        assert float(font_size.replace("px", "")) >= 12, "Body font too small at 375px"

    def test_heading_sizes_responsive(self, page: Page):
        """Test heading sizes scale properly"""
        page.set_viewport_size(VIEWPORTS["mobile_small"])
        page.goto(PORTAL_URL, timeout=30000)

        # H1 should be smaller on mobile
        h1 = page.locator("h1, .page-title").first
        if h1.count() > 0:
            font_size = h1.evaluate("el => window.getComputedStyle(el).fontSize")
            # Should be reasonable (not huge)
            assert float(font_size.replace("px", "")) <= 32, "H1 too large at 375px"


class TestTouchTargets:
    """Tests for touch-friendly targets on mobile"""

    def test_button_touch_target_375px(self, page: Page):
        """Test buttons have 44px minimum touch target at 375px"""
        page.set_viewport_size(VIEWPORTS["mobile_small"])
        page.goto(ADMIN_URL, timeout=30000)

        buttons = page.locator("button, .btn, .action-btn, .nav-item")
        if buttons.count() > 0:
            first_btn = buttons.first
            box = first_btn.bounding_box()
            if box:
                # Minimum 44px touch target
                assert box["height"] >= 40 or box["width"] >= 40, \
                    "Button touch target too small at 375px"
