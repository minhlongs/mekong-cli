# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and export renderers (JSON, CSV, PDF/HTML) for AuditExporter."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Literal, Optional

ExportFormat = Literal["csv", "json", "pdf"]


@dataclass
class ExportFilter:
    """Filter criteria for audit log export."""

    date_from: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    date_to: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    license_key: Optional[str] = None
    event_type: Optional[str] = None
    tenant_id: Optional[str] = None
    limit: int = 10000


class AuditExportRenderersMixin:
    """Formatting and export methods for AuditExporter."""

    def _generate_summary(self, events: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Generate summary statistics for exported data."""
        return {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "violation_count": len(events["violation_events"]),
            "rate_limit_count": len(events["rate_limit_events"]),
            "validation_count": len(events["validation_logs"]),
            "total_records": sum(len(v) for v in events.values()),
        }

    async def export_json(self, filters: ExportFilter, include_summary: bool = True) -> str:
        """Export audit logs to JSON format."""
        events = await self.query_events(filters)  # type: ignore[attr-defined]
        output: Dict[str, Any] = {"events": events}
        if include_summary:
            output["summary"] = self._generate_summary(events)
        return json.dumps(output, indent=2, default=str)

    async def export_csv(self, filters: ExportFilter, output_path: str) -> str:
        """Export audit logs to CSV format."""
        events = await self.query_events(filters)  # type: ignore[attr-defined]
        for event_type, records in events.items():
            if not records:
                continue
            with open(f"{output_path}_{event_type}.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)

        summary = self._generate_summary(events)
        with open(f"{output_path}_summary.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Value"])
            for key, value in summary.items():
                writer.writerow([key, value])
            writer.writerow(["Generated At", datetime.now(timezone.utc).isoformat()])

        return output_path

    async def export_pdf(
        self, filters: ExportFilter, output_path: str, title: str = "Compliance Audit Report"
    ) -> str:
        """Export audit logs to PDF format (falls back to HTML)."""
        events = await self.query_events(filters)  # type: ignore[attr-defined]
        summary = self._generate_summary(events)
        html_content = self._generate_html_report(events, summary, title)

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table

            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = [
                Paragraph(title, styles["Heading1"]),
                Spacer(1, 12),
                Paragraph("Summary Statistics", styles["Heading2"]),
                Table([[k, str(v)] for k, v in summary.items()]),
                Spacer(1, 12),
            ]

            for event_type, records in events.items():
                story.append(Paragraph(f"{event_type.replace('_', ' ').title()}: {len(records)} records", styles["Heading3"]))
                for record in records[:50]:
                    record_text = " | ".join(f"{k}: {v}" for k, v in list(record.items())[:5])
                    story.append(Paragraph(record_text, styles["Normal"]))
                if len(records) > 50:
                    story.append(Paragraph(f"... and {len(records) - 50} more records", styles["Italic"]))
                story.append(Spacer(1, 12))

            doc.build(story)
            return output_path
        except ImportError:
            html_path = output_path.replace(".pdf", ".html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            return html_path

    def _generate_html_report(
        self, events: Dict[str, List[Dict[str, Any]]], summary: Dict[str, Any], title: str
    ) -> str:
        """Generate HTML report content."""
        rows_summary = "".join(
            f"            <tr><td>{k}</td><td>{v}</td></tr>\n"
            for k, v in summary.items() if k != "export_timestamp"
        )
        html = (
            f"<!DOCTYPE html>\n<html>\n<head>\n    <title>{title}</title>\n    <style>\n"
            "        body { font-family: Arial, sans-serif; margin: 40px; }\n"
            "        h1 { color: #333; }\n"
            "        h2 { color: #666; border-bottom: 1px solid #ccc; }\n"
            "        table { border-collapse: collapse; width: 100%; margin: 20px 0; }\n"
            "        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }\n"
            "        th { background-color: #4CAF50; color: white; }\n"
            "        tr:nth-child(even) { background-color: #f2f2f2; }\n"
            "        .summary { background: #f9f9f9; padding: 20px; border-radius: 5px; }\n"
            "        .timestamp { color: #999; font-size: 12px; }\n"
            "    </style>\n</head>\n<body>\n"
            f"    <h1>{title}</h1>\n"
            f'    <p class="timestamp">Generated: {summary["export_timestamp"]}</p>\n\n'
            '    <div class="summary">\n        <h2>Summary</h2>\n        <table>\n'
            "            <tr><th>Metric</th><th>Value</th></tr>\n"
            f"{rows_summary}        </table>\n    </div>\n"
        )

        for event_type, records in events.items():
            html += f"\n    <h2>{event_type.replace('_', ' ').title()} ({len(records)} records)</h2>\n"
            if records:
                cols = list(records[0].keys())[:8]
                headers = "".join(f"            <th>{c}</th>\n" for c in cols)
                html += f"    <table>\n        <tr>\n{headers}        </tr>\n"
                for record in records[:100]:
                    html += "        <tr>\n"
                    for col in list(record.keys())[:8]:
                        raw = str(record[col])
                        val = raw[:50] + "..." if len(raw) > 50 else record[col]
                        html += f"            <td>{val}</td>\n"
                    html += "        </tr>\n"
                html += "    </table>\n"
                if len(records) > 100:
                    html += f"    <p><em>... and {len(records) - 100} more records</em></p>\n"

        return html + "\n</body>\n</html>"

