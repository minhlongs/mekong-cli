"""E2E test configuration for Mekong CLI."""

import pytest
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from src.gateway import app


# Playwright fixtures
@pytest.fixture(scope="session")
def browser():
    """Create a browser instance for E2E tests."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser: Browser) -> Page:
    """Create a new page for each test."""
    context: BrowserContext = browser.new_context(
        viewport={"width": 1920, "height": 1080}
    )
    page: Page = context.new_page()
    yield page
    context.close()


# FastAPI test client
@pytest.fixture
def client():
    """Create a TestClient for the FastAPI gateway app."""
    with TestClient(app) as c:
        yield c
