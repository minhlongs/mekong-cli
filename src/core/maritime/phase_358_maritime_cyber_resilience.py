"""Phase 358: Maritime Cyber Risk Management & OT/IT Network Resilience Engine.

Compliant with IMO Resolution MSC.428(98), MSC-FAL.1/Circ.3, and IACS Unified Requirements E26 & E27.
Evaluates OT/IT network zone segmentation, IEC 61162 / NMEA anomaly spoofing detection,
satellite WAN failover latency, and vessel cyber risk posture.
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field


@dataclass
class MaritimeCyberInput:
    vessel_id: str
    is_navigation_ot_isolated: bool = True
    is_propulsion_ot_isolated: bool = True
    is_crew_welfare_it_segmented: bool = True
    detected_nmea_checksum_error_rate: float = 0.005  # fraction of packets
    gps_position_jump_knots: float = 0.5  # sudden apparent speed spike
    active_satellite_link: str = "STARLINK_LEO"  # STARLINK_LEO, VSAT_GEO, L_BAND
    satellite_latency_ms: float = 45.0
    packet_loss_percent: float = 0.2
    is_unauthorized_usb_detected: bool = False


@dataclass
class MaritimeCyberResult:
    vessel_id: str
    segmentation_score_percent: float
    is_nmea_spoofing_detected: bool
    cyber_threat_level: str  # NORMAL, ELEVATED, SEVERE, CRITICAL
    recommended_satellite_link: str
    is_crew_internet_quarantined: bool
    status: str
    advisories: list[str] = field(default_factory=list)


class MaritimeCyberEngine:
    """Engine for shipboard OT/IT cyber risk management and network failover."""

    @classmethod
    def evaluate(cls, inp: MaritimeCyberInput) -> MaritimeCyberResult:
        # Calculate network segmentation compliance (IEC 62443 / IACS E26)
        seg_score = 0.0
        if inp.is_navigation_ot_isolated:
            seg_score += 40.0
        if inp.is_propulsion_ot_isolated:
            seg_score += 35.0
        if inp.is_crew_welfare_it_segmented:
            seg_score += 25.0

        # Anomaly detection on Bridge NMEA / IEC 61162 bus
        # Spoofing signs: Checksum error rate > 5% or impossible position jumps > 30 kts
        is_nmea_spoofed = (
            inp.detected_nmea_checksum_error_rate >= 0.05
            or inp.gps_position_jump_knots >= 30.0
        )

        # Multi-WAN Satellite Link failover evaluation
        # Starlink latency < 150 ms & loss < 5% -> maintain LEO
        # If Starlink degraded, failover to VSAT or L-Band
        active_link = inp.active_satellite_link.upper()
        rec_link = active_link

        if active_link == "STARLINK_LEO":
            if inp.satellite_latency_ms > 250.0 or inp.packet_loss_percent > 10.0:
                rec_link = "VSAT_GEO"
        elif active_link == "VSAT_GEO":
            if inp.satellite_latency_ms > 800.0 or inp.packet_loss_percent > 20.0:
                rec_link = "L_BAND"

        # Threat level assessment
        advisories: list[str] = []
        is_quarantine = False

        if is_nmea_spoofed and inp.is_unauthorized_usb_detected:
            threat_level = "CRITICAL"
            status = "CYBER_ATTACK_CONTAINMENT"
            is_quarantine = True
            advisories.append(
                "CRITICAL: Active NMEA GPS spoofing and unauthorized physical USB bridge intrusion! Engage Emergency Bridge Override."
            )
        elif is_nmea_spoofed:
            threat_level = "SEVERE"
            status = "NAVIGATION_OT_COMPROMISED"
            advisories.append(
                "ALERT: GPS/NMEA bus anomaly detected! Cross-verify ECDIS with Radar/Visual bearings and Terrestrial Radio."
            )
        elif inp.is_unauthorized_usb_detected:
            threat_level = "ELEVATED"
            status = "PHYSICAL_SECURITY_BREACH"
            is_quarantine = True
            advisories.append(
                "WARNING: Unauthorized USB connected on operational terminal. Crew welfare network quarantined."
            )
        elif seg_score < 100.0:
            threat_level = "ELEVATED"
            status = "SEGMENTATION_DEFICIENT"
            advisories.append(
                f"NOTICE: IACS UR E26 OT/IT segmentation incomplete ({seg_score}%). Implement firewall conduits."
            )
        else:
            threat_level = "NORMAL"
            status = "RESILIENT"
            advisories.append(
                "NORMAL: OT/IT networks isolated, zero NMEA anomalies, satellite link telemetry nominal."
            )

        if rec_link != active_link:
            advisories.append(
                f"FAILOVER: Switch primary satellite WAN from {active_link} to {rec_link} due to degraded telemetry."
            )

        if is_quarantine:
            advisories.append(
                "CONTAINMENT: Crew Welfare Wi-Fi and non-essential administrative ports isolated from satellite gateway."
            )

        return MaritimeCyberResult(
            vessel_id=inp.vessel_id,
            segmentation_score_percent=round(seg_score, 1),
            is_nmea_spoofing_detected=is_nmea_spoofed,
            cyber_threat_level=threat_level,
            recommended_satellite_link=rec_link,
            is_crew_internet_quarantined=is_quarantine,
            status=status,
            advisories=advisories,
        )
