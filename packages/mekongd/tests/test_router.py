"""Router policy unit tests."""

from __future__ import annotations

import pytest

from mekongd.config import PolicyConfig
from mekongd.router import Router
from mekongd.schemas import MessagesRequest


@pytest.fixture
def router() -> Router:
    return Router(PolicyConfig())


def _req(system: str | None = None, user: str = "") -> MessagesRequest:
    return MessagesRequest(
        model="claude-opus-4-7",
        system=system,
        messages=[{"role": "user", "content": user}],
    )


def test_local_on_read(router: Router):
    d = router.decide(_req(system="Read the repo and summarize"))
    assert d.destination == "local"


def test_cloud_on_plan(router: Router):
    d = router.decide(_req(system="Plan the migration and output ADR"))
    assert d.destination == "cloud"


def test_cloud_precedence_over_local(router: Router):
    # "review" (cloud) should beat "rewrite" (local)
    d = router.decide(_req(system="Review then rewrite this module"))
    assert d.destination == "cloud"


def test_default_local(router: Router):
    d = router.decide(_req(user="???"))
    assert d.destination == "local"
    assert "default" in d.reason


def test_custom_policy_default_cloud():
    policy = PolicyConfig(
        local_patterns=[],
        cloud_patterns=[],
        default_destination="cloud",
    )
    d = Router(policy).decide(_req(user="anything"))
    assert d.destination == "cloud"
