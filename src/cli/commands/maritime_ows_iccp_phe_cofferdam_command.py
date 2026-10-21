"""Typer CLI commands for Maritime Phases 391-394.

Includes OWS 15 ppm, ICCP Cathodic Protection, Central Titanium PHE,
and Chemical Tanker Cofferdam Vapor Sniffing.
Strictly < 200 LOC, zero mocks.
"""

import typer
from rich.console import Console
from rich.table import Table

from src.core.maritime.phase_391_oily_water_separator_ceramic import (
    OilyWaterSeparatorEngine,
    OilyWaterSeparatorInput,
)
from src.core.maritime.phase_392_iccp_cathodic_protection_shaft import (
    IccpCathodicProtectionEngine,
    IccpCathodicProtectionInput,
)
from src.core.maritime.phase_393_central_titanium_phe_ultrasonic import (
    CentralTitaniumPheEngine,
    CentralTitaniumPheInput,
)
from src.core.maritime.phase_394_chemical_cofferdam_vapor_inerting import (
    ChemicalCofferdamEngine,
    ChemicalCofferdamInput,
)

console = Console()

ows_app = typer.Typer(help="Phase 391: Oily Water Separator 15 ppm & Ceramic Membrane (MEPC.107(49))")
iccp_app = typer.Typer(help="Phase 392: ICCP Hull Cathodic Protection & Shaft Grounding (DNV-RP-B401)")
phe_app = typer.Typer(help="Phase 393: Central Titanium Plate Heat Exchanger & Ultrasonic Clean (TEMA R)")
cofferdam_app = typer.Typer(help="Phase 394: Chemical Tanker Cofferdam Vapor Sniffing & Inerting (IBC Code)")


@ows_app.callback(invoke_without_command=True)
def evaluate_ows(
    oil_ppm: float = typer.Option(8.5, "--oil-ppm", help="Bilge oil content in ppm"),
    flow_m3_h: float = typer.Option(2.5, "--flow-m3-h", help="Feed flow rate in m3/h"),
    tmp_bar: float = typer.Option(1.2, "--tmp-bar", help="Transmembrane pressure in bar"),
    en_route: bool = typer.Option(True, "--en-route/--not-en-route", help="Vessel is underway en route"),
    in_port: bool = typer.Option(False, "--in-port/--at-sea", help="Vessel in port or at anchor"),
):
    """Evaluate OWS 15 ppm bilge separator compliance under MARPOL Annex I."""
    inp = OilyWaterSeparatorInput(
        bilge_oil_content_ppm=oil_ppm,
        feed_flow_rate_m3_h=flow_m3_h,
        transmembrane_pressure_bar=tmp_bar,
        vessel_en_route=en_route,
        in_port_or_anchor=in_port,
    )
    res = OilyWaterSeparatorEngine().evaluate(inp)

    table = Table(title="Maritime Phase 391: Oily Water Separator MEPC.107(49)")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value / Status", style="magenta")
    table.add_row("Oil Content (ppm)", str(res.oil_content_ppm))
    table.add_row("Alarm Status", res.alarm_status)
    table.add_row("Three-Way Valve Command", res.three_way_valve_command)
    table.add_row("Discharge Permitted", "YES" if res.discharge_permitted else "NO")
    table.add_row("Membrane Status", res.membrane_fouling_status)
    table.add_row("Regulatory Classification", res.regulatory_status)
    console.print(table)


@iccp_app.callback(invoke_without_command=True)
def evaluate_iccp(
    potential_mv: float = typer.Option(-880.0, "--potential-mv", help="Hull potential vs Ag/AgCl in mV"),
    shaft_mv: float = typer.Option(25.0, "--shaft-mv", help="Shaft-to-hull potential in mV"),
    anode_amps: float = typer.Option(35.0, "--anode-amps", help="Current anode output in Amperes"),
):
    """Evaluate ICCP cathodic protection and shaft slip-ring grounding under DNV-RP-B401."""
    inp = IccpCathodicProtectionInput(
        hull_potential_mv=potential_mv,
        shaft_to_hull_voltage_mv=shaft_mv,
        anode_output_current_amps=anode_amps,
    )
    res = IccpCathodicProtectionEngine().evaluate(inp)

    table = Table(title="Maritime Phase 392: ICCP Protection & Shaft Grounding")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value / Status", style="green")
    table.add_row("Hull Potential", f"{res.hull_potential_mv} mV")
    table.add_row("Protection Status", res.protection_status)
    table.add_row("Shaft Grounding Status", res.shaft_grounding_status)
    table.add_row("Recommended Anode Current", f"{res.recommended_anode_current_a} A")
    table.add_row("Hydrogen Embrittlement Risk", "YES" if res.hydrogen_embrittlement_risk else "NO")
    table.add_row("Corrosion Activity Risk", "YES" if res.corrosion_activity_risk else "NO")
    console.print(table)


@phe_app.callback(invoke_without_command=True)
def evaluate_phe(
    fw_in_c: float = typer.Option(48.0, "--fw-in-c", help="Central FW inlet temperature °C"),
    fw_out_c: float = typer.Option(36.0, "--fw-out-c", help="Central FW outlet temperature °C"),
    sw_in_c: float = typer.Option(28.0, "--sw-in-c", help="Seawater inlet temperature °C"),
    sw_out_c: float = typer.Option(34.0, "--sw-out-c", help="Seawater outlet temperature °C"),
    dp_bar: float = typer.Option(0.65, "--dp-bar", help="Plate pressure drop in bar"),
    us_intensity: float = typer.Option(1.8, "--us-w-cm2", help="Ultrasonic intensity in W/cm2"),
):
    """Evaluate Central Titanium Plate Heat Exchanger & Ultrasonic Clean under TEMA Class R."""
    inp = CentralTitaniumPheInput(
        hot_side_inlet_temp_c=fw_in_c,
        hot_side_outlet_temp_c=fw_out_c,
        cold_side_inlet_temp_c=sw_in_c,
        cold_side_outlet_temp_c=sw_out_c,
        pressure_drop_bar=dp_bar,
        ultrasonic_intensity_w_cm2=us_intensity,
    )
    res = CentralTitaniumPheEngine().evaluate(inp)

    table = Table(title="Maritime Phase 393: Central Titanium PHE & Ultrasonic Clean")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value / Status", style="yellow")
    table.add_row("Heat Duty (kW)", f"{res.heat_duty_kw} kW")
    table.add_row("LMTD", f"{res.lmtd_c} °C")
    table.add_row("Thermal Performance", res.thermal_performance)
    table.add_row("Pressure Drop Status", res.pressure_drop_status)
    table.add_row("Ultrasonic Prevention", res.ultrasonic_biofilm_prevention)
    table.add_row("Maintenance Action", res.maintenance_action)
    console.print(table)


@cofferdam_app.callback(invoke_without_command=True)
def evaluate_cofferdam(
    lel_pct: float = typer.Option(2.0, "--lel-pct", help="Hydrocarbon concentration % LEL"),
    toxic_ppm: float = typer.Option(0.5, "--toxic-ppm", help="Toxic chemical vapor in ppm"),
    o2_pct: float = typer.Option(4.2, "--o2-pct", help="Oxygen concentration % vol"),
    dp_kpa: float = typer.Option(0.35, "--dp-kpa", help="Differential overpressure in kPa"),
):
    """Evaluate Chemical Tanker Cofferdam Vapor Sniffing & Inerting under IBC Code Ch. 15."""
    inp = ChemicalCofferdamInput(
        voc_hydrocarbon_lel_pct=lel_pct,
        toxic_vapor_ppm=toxic_ppm,
        oxygen_concentration_pct=o2_pct,
        cofferdam_diff_pressure_kpa=dp_kpa,
    )
    res = ChemicalCofferdamEngine().evaluate(inp)

    table = Table(title="Maritime Phase 394: Chemical Tanker Cofferdam Vapor Sniffing")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value / Status", style="blue")
    table.add_row("Cofferdam Safety Status", res.cofferdam_safety_status)
    table.add_row("Inerting Compliant", "YES" if res.inerting_compliant else "NO")
    table.add_row("Positive Pressure Barrier", "YES" if res.positive_pressure_intact else "NO")
    table.add_row("N2 Purge Required", "YES" if res.nitrogen_purge_required else "NO")
    table.add_row("Cargo Breach Detected", "YES" if res.chemical_breach_detected else "NO")
    console.print(table)
