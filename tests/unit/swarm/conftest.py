# Skip all swarm tests if required dependencies are not installed.
# Swarm tests require: falkordb
import pytest

falkordb = pytest.importorskip(
    "falkordb",
    reason="falkordb not installed, skipping swarm tests",
)
