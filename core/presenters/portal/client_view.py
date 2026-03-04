"""
Formatting logic for Client views in the portal.
"""
from typing import List

from .entities_proxy import Client, ClientStatus, Invoice, Project


class ClientViewPresenter:
    def format_client_summary(self, client: Client, projects: List[Project], invoices: List[Invoice]) -> str:
        lines = ["╔═══════════════════════════════════════════════════════════╗", f"║  👥 CLIENT PORTAL - {client.company[:30]:<30}  ║", "╠═══════════════════════════════════════════════════════════╣", f"║  Contact: {client.name:<25} Status: {client.status.value:<10}  ║", "║  ───────────────────────────────────────────────────────  ║", "║  📊 ACTIVE PROJECTS:                                      ║"]
        for project in projects:
            lines.append(f"║    • {project.name[:20]:<20} │ Progress: {project.progress:>3.0f}% │ {project.status.value:<10} ║")
        lines.extend(["║                                                           ║", "║  💰 FINANCIALS:                                           ║", f"║    Total Invoiced: ${sum(i.amount for i in invoices):>10,.2f}                    ║", f"║    Total Paid:     ${client.total_spent:>10,.2f}                    ║", "║                                                           ║", "║  [📂 Files]  [💬 Messages]  [📅 Meetings]  [💳 Billing]  ║", "╚═══════════════════════════════════════════════════════════╝"])
        return "\n".join(lines)

    def format_client_list(self, clients: List[Client]) -> str:
        if not clients: return "No clients found."
        lines = ["👥 Client List:", "=" * 60]
        status_icons = { ClientStatus.LEAD: "🎯", ClientStatus.PROSPECT: "🔍", ClientStatus.ACTIVE: "✅", ClientStatus.PAUSED: "⏸️", ClientStatus.CHURNED: "❌" }
        for client in clients:
            icon = status_icons.get(client.status, "❓")
            lines.append(f"{icon} {client.company} - {client.name} ({client.email})\n   Monthly: ${client.monthly_retainer:,.2f} | Total: ${client.total_spent:,.2f}\n")
        return "\n".join(lines)
