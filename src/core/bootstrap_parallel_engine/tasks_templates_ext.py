"""Extended domain template scaffolding helpers (fintech and agent presets)."""

from __future__ import annotations

from .models import BootstrapContext


def _scaffold_fintech(context: BootstrapContext) -> None:
    context.write_file("src/fintech/__init__.py", '"""Fintech Payment Module."""\n')
    context.write_file(
        "src/fintech/vietqr.py",
        '''"""VietQR EMVCo specification generator."""
def generate_vietqr_payload(bank_bin: str, account_number: str, amount: float, memo: str = "") -> str:
    return f"00020101021238570010A00000072701270006{bank_bin}01{len(account_number):02d}{account_number}54{len(str(int(amount))):02d}{int(amount)}5802VN62{len(memo):02d}{memo}6304"
''',
    )
    context.write_file(
        "src/fintech/napas247.py",
        '''"""NAPAS 24/7 instant payment reconciliation."""
from typing import Dict, Any

def reconcile_transaction(tx_id: str, status: str) -> Dict[str, Any]:
    return {"tx_id": tx_id, "reconciled": status == "SUCCESS", "status": status}
''',
    )
    context.write_file(
        "src/fintech/pci_tokens.py",
        '''"""PCI-DSS compliant token masking."""
def mask_card(card_number: str) -> str:
    clean = card_number.replace(" ", "").replace("-", "")
    if len(clean) < 10:
        return "****"
    return f"{clean[:6]}******{clean[-4:]}"
''',
    )
    context.write_file(
        "tests/test_fintech.py",
        '''"""Tests for fintech payment module."""
from src.fintech.vietqr import generate_vietqr_payload
from src.fintech.napas247 import reconcile_transaction
from src.fintech.pci_tokens import mask_card

def test_vietqr():
    payload = generate_vietqr_payload("970415", "123456789", 50000.0, "Coffee")
    assert "970415" in payload
    assert "123456789" in payload

def test_reconciliation():
    res = reconcile_transaction("TX1001", "SUCCESS")
    assert res["reconciled"] is True

def test_mask_card():
    assert mask_card("4111222233334444") == "411122******4444"
''',
    )


def _scaffold_agent(context: BootstrapContext) -> None:
    context.write_file("src/agents/__init__.py", '"""Agent Swarm Architecture."""\n')
    context.write_file(
        "src/agents/swarm.py",
        '''"""Agent Swarm coordinator."""
from typing import List, Dict, Any

class AgentSwarm:
    def __init__(self) -> None:
        self.agents: Dict[str, Dict[str, Any]] = {}

    def register_agent(self, agent_id: str, role: str, capabilities: List[str]) -> None:
        self.agents[agent_id] = {"id": agent_id, "role": role, "capabilities": capabilities}

    def dispatch(self, task_type: str) -> List[str]:
        return [aid for aid, a in self.agents.items() if task_type in a["capabilities"]]
''',
    )
    context.write_file(
        "src/agents/memory_mesh.py",
        '''"""Federated Memory Mesh for autonomous agents."""
from typing import Dict, Any, Optional

class MemoryMesh:
    def __init__(self) -> None:
        self.store: Dict[str, Any] = {}

    def recall(self, key: str) -> Optional[Any]:
        return self.store.get(key)

    def remember(self, key: str, value: Any) -> None:
        self.store[key] = value
''',
    )
    context.write_file(
        "src/agents/agi_loop.py",
        '''"""Autonomous AGI Plan-Execute-Verify loop runner."""
from typing import Dict, Any

class AgiLoop:
    def __init__(self, agent_name: str = "SoloCEO") -> None:
        self.agent_name = agent_name
        self.cycles = 0

    def step(self, goal: str) -> Dict[str, Any]:
        self.cycles += 1
        return {"cycle": self.cycles, "goal": goal, "status": "completed"}
''',
    )
    context.write_file(
        "tests/test_agent.py",
        '''"""Tests for agent module."""
from src.agents.swarm import AgentSwarm
from src.agents.memory_mesh import MemoryMesh
from src.agents.agi_loop import AgiLoop

def test_swarm():
    swarm = AgentSwarm()
    swarm.register_agent("ceo", "CEO", ["plan", "decide"])
    assert swarm.dispatch("plan") == ["ceo"]

def test_memory():
    mesh = MemoryMesh()
    mesh.remember("key1", "val1")
    assert mesh.recall("key1") == "val1"

def test_agi_loop():
    loop = AgiLoop()
    res = loop.step("Run bootstrap")
    assert res["status"] == "completed"
''',
    )
