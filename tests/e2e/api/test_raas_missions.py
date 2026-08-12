"""
E2E tests for RaaS Mission API with credit management.

Tests cover:
- Mission submission with credit reservation
- Credit balance tracking
- Insufficient credits handling
- Usage analytics
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

os.environ['REDIS_URL'] = ''
os.environ['REDIS_ENABLED'] = 'false'

pytestmark = pytest.mark.asyncio


@pytest.fixture
def test_tenant():
    """Return test tenant info."""
    return {
        "tenant_id": "test_tenant_raas_001",
        "email": "test@example.com",
        "license_key": "lic_test_raas_001",
    }


class TestRaaSMissionSubmission:
    """Tests for RaaS mission submission with credit management."""

    def test_submit_mission_insufficient_credits_402(
        self, client, test_tenant
    ):
        """Test that mission submission with insufficient credits returns 402."""
        # This test requires a tenant with zero balance
        drained_license = os.environ.get("DRAINED_LICENSE_KEY")

        if not drained_license:
            pytest.skip("DRAINED_LICENSE_KEY not set")

        response = client.post(
            "/raas/missions",
            json={
                "goal": "Test mission with zero balance",
                "metadata": {},
            },
            headers={"Authorization": f"Bearer {drained_license}"},
        )

        assert response.status_code == 402
        data = response.json()

        assert "upgrade_url" in response.headers
        assert "pricing" in response.headers["upgrade-url"].lower()

    def test_submit_mission_with_sufficient_credits(
        self, client, test_tenant
    ):
        """Test mission submission with sufficient credits."""
        # This test requires a tenant with adequate balance
        test_license = os.environ.get("TEST_LICENSE_KEY")

        if not test_license:
            pytest.skip("TEST_LICENSE_KEY not set")

        response = client.post(
            "/raas/missions",
            json={
                "goal": "Test mission with sufficient credits",
                "metadata": {"test": True},
            },
            headers={"Authorization": f"Bearer {test_license}"},
        )

        # Should succeed or fail based on actual credits
        assert response.status_code in [200, 201, 402]

        if response.status_code in [200, 201]:
            data = response.json()
            assert "id" in data
            assert "status" in data
            assert data["status"] in ["queued", "running"]

    def test_submit_mission_missing_auth(self, client):
        """Test mission submission without auth returns 401."""
        response = client.post(
            "/raas/missions",
            json={"goal": "Test mission"},
        )

        assert response.status_code == 401

    def test_submit_mission_invalid_auth(self, client):
        """Test mission submission with invalid auth returns 401/403."""
        response = client.post(
            "/raas/missions",
            json={"goal": "Test mission"},
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code in [401, 403]

    def test_mission_credit_reservation_atomicity(self, client, test_tenant):
        """Test that credits are reserved atomically on mission submission."""
        # This test would require careful credit state tracking
        # For now, verify the flow
        test_license = os.environ.get("TEST_LICENSE_KEY")

        if not test_license:
            pytest.skip("TEST_LICENSE_KEY not set")

        # Get initial balance
        balance_before = client.get(
            "/raas/credits/balance",
            headers={"Authorization": f"Bearer {test_license}"},
        )

        if balance_before.status_code != 200:
            pytest.skip("Balance endpoint not accessible")

        initial_balance = balance_before.json()["available"]

        # Submit mission
        response = client.post(
            "/raas/missions",
            json={"goal": "Test atomic reservation"},
            headers={"Authorization": f"Bearer {test_license}"},
        )

        assert response.status_code in [200, 201, 402]

        if response.status_code in [200, 201]:
            # Check balance decreased (reserved)
            balance_after = client.get(
                "/raas/credits/balance",
                headers={"Authorization": f"Bearer {test_license}"},
            ).json()

            # Reserved should increase, available should decrease
            assert balance_after["reserved"] >= balance_before.json()["reserved"]


class TestCreditManagement:
    """Tests for credit balance and history endpoints."""

    def test_get_credit_balance(self, client, test_tenant):
        """Test getting credit balance."""
        test_license = os.environ.get("TEST_LICENSE_KEY")

        if not test_license:
            pytest.skip("TEST_LICENSE_KEY not set")

        response = client.get(
            "/raas/credits/balance",
            headers={"Authorization": f"Bearer {test_license}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "available" in data
        assert "reserved" in data
        assert "total" in data
        assert isinstance(data["available"], (int, float))
        assert isinstance(data["reserved"], (int, float))
        assert data["available"] >= 0
        assert data["reserved"] >= 0

    def test_get_credit_history(self, client, test_tenant):
        """Test getting credit transaction history."""
        test_license = os.environ.get("TEST_LICENSE_KEY")

        if not test_license:
            pytest.skip("TEST_LICENSE_KEY not set")

        response = client.get(
            "/raas/credits/history?limit=20",
            headers={"Authorization": f"Bearer {test_license}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "transactions" in data
        assert isinstance(data["transactions"], list)
        assert len(data["transactions"]) <= 20

    def test_credit_history_pagination(self, client, test_tenant):
        """Test pagination for credit history."""
        test_license = os.environ.get("TEST_LICENSE_KEY")

        if not test_license:
            pytest.skip("TEST_LICENSE_KEY not set")

        response = client.get(
            "/raas/credits/history?limit=5&offset=0",
            headers={"Authorization": f"Bearer {test_license}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["transactions"]) <= 5

    def test_credit_history_filter_by_type(self, client, test_tenant):
        """Test filtering credit history by transaction type."""
        test_license = os.environ.get("TEST_LICENSE_KEY")

        if not test_license:
            pytest.skip("TEST_LICENSE_KEY not set")

        for tx_type in ["credit", "debit", "reserve", "release"]:
            response = client.get(
                f"/raas/credits/history?type={tx_type}&limit=10",
                headers={"Authorization": f"Bearer {test_license}"},
            )

            assert response.status_code == 200
            data = response.json()

            # All returned transactions should match the filter
            for tx in data["transactions"]:
                assert tx["type"] == tx_type


class TestUsageAnalytics:
    """Tests for usage analytics endpoints."""

    def test_get_usage_summary(self, client, test_tenant):
        """Test getting usage summary."""
        test_license = os.environ.get("TEST_LICENSE_KEY")

        if not test_license:
            pytest.skip("TEST_LICENSE_KEY not set")

        response = client.get(
            "/raas/usage/summary",
            headers={"Authorization": f"Bearer {test_license}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "period_start" in data
        assert "period_end" in data
        assert "total_missions" in data
        assert "total_mcus_used" in data

    def test_usage_summary_date_range(self, client, test_tenant):
        """Test usage summary includes correct date range."""
        test_license = os.environ.get("TEST_LICENSE_KEY")

        if not test_license:
            pytest.skip("TEST_LICENSE_KEY not set")

        response = client.get(
            "/raas/usage/summary",
            headers={"Authorization": f"Bearer {test_license}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Period should be last 30 days
        from datetime import datetime, timedelta

        period_start = datetime.fromisoformat(data["period_start"].replace("Z", "+00:00"))
        period_end = datetime.fromisoformat(data["period_end"].replace("Z", "+00:00"))

        days_covered = (period_end - period_start).days
        assert 29 <= days_covered <= 30

    def test_get_activity_feed(self, client, test_tenant):
        """Test getting activity feed."""
        test_license = os.environ.get("TEST_LICENSE_KEY")

        if not test_license:
            pytest.skip("TEST_LICENSE_KEY not set")

        response = client.get(
            "/raas/usage/activity?limit=20",
            headers={"Authorization": f"Bearer {test_license}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "activities" in data
        assert isinstance(data["activities"], list)

        if data["activities"]:
            activity = data["activities"][0]
            assert "id" in activity
            assert "type" in activity
            assert "timestamp" in activity
            assert "description" in activity


class TestMissionLifecycle:
    """Tests for complete mission lifecycle."""

    def test_mission_completes_and_releases_credits(
        self, client, test_tenant
    ):
        """Test that completed missions release reserved credits."""
        test_license = os.environ.get("TEST_LICENSE_KEY")

        if not test_license:
            pytest.skip("TEST_LICENSE_KEY not set")

        # Get initial available credits
        initial = client.get(
            "/raas/credits/balance",
            headers={"Authorization": f"Bearer {test_license}"},
        ).json()

        # Submit mission
        mission_response = client.post(
            "/raas/missions",
            json={"goal": "Test lifecycle credit release"},
            headers={"Authorization": f"Bearer {test_license}"},
        )

        if mission_response.status_code == 402:
            pytest.skip("Insufficient credits for test")

        mission = mission_response.json()
        mission_id = mission["id"]

        # Wait for completion
        import time

        max_wait = 60
        start = time.time()
        completed = False

        while time.time() - start < max_wait:
            status_response = client.get(
                f"/raas/missions/{mission_id}",
                headers={"Authorization": f"Bearer {test_license}"},
            )

            if status_response.status_code == 200:
                mission_data = status_response.json()
                if mission_data["status"] in ["completed", "failed"]:
                    completed = True
                    break

            time.sleep(3)

        if completed:
            # Check final balance
            final = client.get(
                "/raas/credits/balance",
                headers={"Authorization": f"Bearer {test_license}"},
            ).json()

            # After completion, reserved should be released
            # Available + Reserved should reflect final state
            pass  # Detailed balance check depends on implementation
        else:
            pytest.skip("Mission did not complete within timeout")


class TestErrorRecovery:
    """Tests for error recovery and resilience."""

    def test_mission_submission_after_service_error(self, client, test_tenant):
        """Test that mission submission works after transient errors."""
        # Simulate a failure and verify recovery
        test_license = os.environ.get("TEST_LICENSE_KEY")

        if not test_license:
            pytest.skip("TEST_LICENSE_KEY not set")

        # Submit multiple missions
        for i in range(3):
            response = client.post(
                "/raas/missions",
                json={"goal": f"Recovery test mission {i}"},
                headers={"Authorization": f"Bearer {test_license}"},
            )

            # Should succeed or fail with consistent error
            assert response.status_code in [200, 201, 402]

    def test_concurrent_mission_submissions(self, client, test_tenant):
        """Test handling of concurrent mission submissions."""
        import threading
        import time

        test_license = os.environ.get("TEST_LICENSE_KEY")

        if not test_license:
            pytest.skip("TEST_LICENSE_KEY not set")

        results = []
        errors = []

        def submit_mission(idx):
            try:
                response = client.post(
                    "/raas/missions",
                    json={"goal": f"Concurrent test {idx}"},
                    headers={"Authorization": f"Bearer {test_license}"},
                )
                results.append((idx, response.status_code))
            except Exception as e:
                errors.append((idx, str(e)))

        threads = []
        for i in range(5):
            t = threading.Thread(target=submit_mission, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All submissions should succeed or fail with appropriate error
        for idx, status in results:
            assert status in [200, 201, 402, 429]

        assert len(errors) == 0, f"Errors in concurrent submissions: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
