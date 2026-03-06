"""
🧲 Client Magnet Persistence Logic
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from .models import Client, Lead, LeadSource, LeadStatus

# Configure logging
logger = logging.getLogger(__name__)


class ClientMagnetPersistence:
    """Handles storage of leads and clients data."""

    def __init__(self, storage_path: Path):
        self.leads_file = storage_path / "leads.json"
        self.clients_file = storage_path / "clients.json"

    def save(self, leads: List[Lead], clients: List[Client]) -> None:
        """Persists leads and clients state to JSON."""
        try:
            self._save_leads(leads)
            self._save_clients(clients)
        except Exception as e:
            logger.error(f"Failed to save client magnet data: {e}")

    def _save_leads(self, leads: List[Lead]) -> None:
        data = {
            "metadata": {"last_updated": datetime.now().isoformat()},
            "leads": [
                {
                    "name": lead.name,
                    "company": lead.company,
                    "email": lead.email,
                    "phone": lead.phone,
                    "source": lead.source.value,
                    "status": lead.status.value,
                    "score": lead.score,
                    "budget": lead.budget,
                    "notes": lead.notes,
                    "created_at": lead.created_at.isoformat(),
                    "metadata": lead.metadata,
                }
                for lead in leads
            ],
        }
        self.leads_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _save_clients(self, clients: List[Client]) -> None:
        data = {
            "metadata": {"last_updated": datetime.now().isoformat()},
            "clients": [
                {
                    "id": client.id,
                    "name": client.name,
                    "company": client.company,
                    "email": client.email,
                    "phone": client.phone,
                    "zalo": client.zalo,
                    "total_ltv": client.total_ltv,
                    "active_projects": client.active_projects,
                    "joined_at": client.joined_at.isoformat(),
                }
                for client in clients
            ],
        }
        self.clients_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self) -> Tuple[List[Lead], List[Client]]:
        """Loads leads and clients state from disk."""
        return self._load_leads(), self._load_clients()

    def _load_leads(self) -> List[Lead]:
        if not self.leads_file.exists():
            return []

        leads = []
        try:
            data = json.loads(self.leads_file.read_text(encoding="utf-8"))
            for lead_dict in data.get("leads", []):
                leads.append(
                    Lead(
                        name=lead_dict["name"],
                        company=lead_dict.get("company", ""),
                        email=lead_dict.get("email", ""),
                        phone=lead_dict.get("phone", ""),
                        source=LeadSource(lead_dict["source"]),
                        status=LeadStatus(lead_dict["status"]),
                        score=lead_dict.get("score", 50),
                        budget=lead_dict.get("budget", 0.0),
                        notes=lead_dict.get("notes", ""),
                        created_at=datetime.fromisoformat(lead_dict["created_at"]),
                        metadata=lead_dict.get("metadata", {}),
                    )
                )
        except Exception as e:
            logger.warning(f"Leads data loading failed: {e}")
        return leads

    def _load_clients(self) -> List[Client]:
        if not self.clients_file.exists():
            return []

        clients = []
        try:
            data = json.loads(self.clients_file.read_text(encoding="utf-8"))
            for client_dict in data.get("clients", []):
                clients.append(
                    Client(
                        id=client_dict["id"],
                        name=client_dict["name"],
                        company=client_dict["company"],
                        email=client_dict["email"],
                        phone=client_dict.get("phone", ""),
                        zalo=client_dict.get("zalo", ""),
                        total_ltv=client_dict.get("total_ltv", 0.0),
                        active_projects=client_dict.get("active_projects", 0),
                        joined_at=datetime.fromisoformat(client_dict["joined_at"]),
                    )
                )
        except Exception as e:
            logger.warning(f"Clients data loading failed: {e}")
        return clients
