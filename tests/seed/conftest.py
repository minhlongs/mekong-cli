"""
Pytest configuration for seed layer tests.

Overrides the parent conftest.py autouse fixtures that require cryptography.
Seed tests are isolated unit tests — no billing DB isolation needed.
"""

import pytest


# Override parent _isolate_billing_db fixture — seed tests don't need it
@pytest.fixture(scope="session", autouse=False)
def _isolate_billing_db():
    """Disabled for seed tests."""
    pass


# Override parent _reset_credit_tables fixture — seed tests don't need it
@pytest.fixture(autouse=False)
def _reset_credit_tables():
    """Disabled for seed tests."""
    pass
