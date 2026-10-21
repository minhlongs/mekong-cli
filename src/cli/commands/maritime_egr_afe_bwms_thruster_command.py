"""Typer CLI commands for Maritime Phases 419-422.

Includes:
- EGR Bleed-off Water Treatment (Phase 419 MEPC.307(73), MARPOL Annex VI)
- Shaft Generator AFE Harmonics & Grid Quality (Phase 420 IACS UR E24, IEEE 519)
- BWMS Electro-Chlorination & Neutralization (Phase 421 IMO BWM D-2, USCG Phase-II)
- Stern Thruster Tunnel Grate & CPP Pitch Cavitation (Phase 422 DNV Pt.4 Ch.5)

Strictly < 200 LOC, zero mocks.
"""

import typer
from rich.console import Console
from rich.table import Table

from src.core.maritime.phase_419_egr_bleedoff_water_treatment import (
    EgrBleedoffTelemetry,
    EgrBleedoffWaterTreatmentEngine,
)
from src.core.maritime.phase_420_shaft_generator_afe_harmonics import (
    ShaftGeneratorAfeHarmonicsEngine,
    ShaftGeneratorAfeTelemetry,
)
from src.core.maritime.phase_421_bwms_chlorination_neutralization import (
    BwmsChlorinationNeutralizationEngine,
    BwmsChlorinationTelemetry,
)
from src.core.maritime.phase_422_stern_thruster_cavitation_pitch import (
    SternThrusterCavitationEngine,
    SternThrusterCavitationTelemetry,
)

console = Console()

egrbleedoff_app = typer.Typer(help="Phase 419: EGR Bleed-off Water Treatment System (MEPC.307(73))")
shaftgenafe_app = typer.Typer(help="Phase 420: Shaft Generator AFE Harmonics & THD (IACS UR E24 / IEEE 519)")
bwmschlorination_app = typer.Typer(help="Phase 421: BWMS Electro-Chlorination & Neutralization (IMO BWM D-2)")
sterncavitation_app = typer.Typer(help="Phase 422: Stern Thruster Grate & CPP Cavitation (DNV Pt.4 Ch.5)")


@egrbleedoff_app.callback(invoke_without_command=True)
def evaluate_egr_bleedoff(
    oil_ppm: float = typer.Option(4.2, "--oil-ppm", help="Oil content in ppm"),
    ph: float = typer.Option(7.35, "--ph", help="Optical pH sensor reading"),
    turbidity: float = typer.Option(12.4, "--turbidity", help="Turbidity in FNU"),
    pah: float = typer.Option(22.0, "--pah", help="PAH concentration ug/L"),
    override: bool = typer.Option(False, "--override", help="Manual divert override"),
):
    """Evaluate EGR Bleed-off Water Treatment compliance and 3-way divert valve position."""
    telem = EgrBleedoffTelemetry(
        oil_content_ppm=oil_ppm,
        ph_value=ph,
        turbidity_fnu=turbidity,
        pah_concentration_ug_l=pah,
        divert_valve_override=override,
    )
    res = EgrBleedoffWaterTreatmentEngine().evaluate(telem)

    table = Table(title="[bold green]EGR Bleed-off Water Treatment (Phase 419)[/bold green]")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="yellow")
    table.add_row("Status", str(res.status))
    table.add_row("Divert Valve Position", str(res.divert_valve_position))
    table.add_row("Oil Compliant (<15 ppm)", str(res.oil_compliant))
    table.add_row("pH Compliant (>=6.5)", str(res.ph_compliant))
    table.add_row("Turbidity Compliant (<=25 FNU)", str(res.turbidity_compliant))
    table.add_row("PAH Compliant (<=50 ug/L)", str(res.pah_compliant))
    table.add_row("Discharge Flow Rate", f"{res.discharge_flow_m3_h} m3/h")
    console.print(table)


@shaftgenafe_app.callback(invoke_without_command=True)
def evaluate_shaft_gen_afe(
    voltage: float = typer.Option(440.0, "--voltage", help="Bus voltage V"),
    h5: float = typer.Option(1.4, "--h5", help="5th harmonic %"),
    h7: float = typer.Option(1.1, "--h7", help="7th harmonic %"),
    unbalance: float = typer.Option(0.85, "--unbalance", help="Voltage unbalance %"),
    dip_ms: float = typer.Option(0.0, "--dip-ms", help="Voltage dip duration ms"),
    rev_power_s: float = typer.Option(0.0, "--rev-power-s", help="Reverse power duration s"),
):
    """Evaluate Shaft Generator AFE harmonic distortion, THD, and trip interlocks."""
    telem = ShaftGeneratorAfeTelemetry(
        bus_voltage_v=voltage,
        harmonic_5th_pct=h5,
        harmonic_7th_pct=h7,
        voltage_unbalance_pct=unbalance,
        voltage_dip_duration_ms=dip_ms,
        reverse_power_duration_s=rev_power_s,
    )
    res = ShaftGeneratorAfeHarmonicsEngine().evaluate(telem)

    table = Table(title="[bold blue]Shaft Generator AFE Grid Harmonics (Phase 420)[/bold blue]")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="yellow")
    table.add_row("Status", str(res.status))
    table.add_row("Voltage THD", f"{res.thd_voltage_pct}% (Limit <= 5.0%)")
    table.add_row("Power Factor", f"{res.power_factor}")
    table.add_row("THD Compliant", str(res.thd_compliant))
    table.add_row("Breaker Status", str(res.breaker_status))
    console.print(table)


@bwmschlorination_app.callback(invoke_without_command=True)
def evaluate_bwms_chlorination(
    mode: str = typer.Option("DEBALLASTING", "--mode", help="BALLASTING or DEBALLASTING"),
    tro: float = typer.Option(0.03, "--tro", help="TRO sensor reading mg/L"),
    current_a: float = typer.Option(1200.0, "--current", help="Electrolytic cell current A"),
    h2_pct: float = typer.Option(0.22, "--h2", help="H2 concentration % vol"),
    blower: bool = typer.Option(True, "--blower/--no-blower", help="Degassing blower running"),
):
    """Evaluate BWMS Electro-Chlorination generation and De-ballasting Neutralization."""
    telem = BwmsChlorinationTelemetry(
        operational_mode=mode,
        tro_sensor_reading_mg_l=tro,
        electrolytic_cell_current_a=current_a,
        cell_hydrogen_pct_vol=h2_pct,
        degassing_blower_running=blower,
    )
    res = BwmsChlorinationNeutralizationEngine().evaluate(telem)

    table = Table(title="[bold magenta]BWMS Chlorination & Neutralization (Phase 421)[/bold magenta]")
    table.add_column("Parameter", style="cyan")
    table.add_column("Reading", style="yellow")
    table.add_row("Status", str(res.status))
    table.add_row("TRO D-2 Compliant", str(res.tro_discharge_compliant))
    table.add_row("Hydrogen Safe (<1.0% vol)", str(res.hydrogen_safety_compliant))
    table.add_row("Cl2 Generation Rate", f"{res.electrolysis_efficiency_kg_cl2_h} kg/h")
    table.add_row("Discharge Interlock Open", str(res.discharge_interlock_open))
    console.print(table)


@sterncavitation_app.callback(invoke_without_command=True)
def evaluate_stern_cavitation(
    rpm: float = typer.Option(240.0, "--rpm", help="Thruster RPM"),
    pitch: float = typer.Option(18.5, "--pitch", help="CPP blade pitch deg"),
    water_v: float = typer.Option(4.5, "--vel", help="Tunnel water velocity m/s"),
    grate_dp: float = typer.Option(0.08, "--grate-dp", help="Grate differential pressure bar"),
    acoustic_db: float = typer.Option(18.2, "--acoustic-db", help="Acoustic sensor dB"),
):
    """Evaluate Stern Thruster Tunnel hydrodynamics, cavitation inception, and pitch derate."""
    telem = SternThrusterCavitationTelemetry(
        thruster_rpm=rpm,
        commanded_pitch_deg=pitch,
        actual_pitch_deg=pitch,
        tunnel_water_velocity_m_s=water_v,
        grate_differential_pressure_bar=grate_dp,
        acoustic_noise_10_40khz_db=acoustic_db,
    )
    res = SternThrusterCavitationEngine().evaluate(telem)

    table = Table(title="[bold yellow]Stern Thruster Tunnel Grate & CPP Cavitation (Phase 422)[/bold yellow]")
    table.add_column("Metric", style="cyan")
    table.add_column("Reading", style="yellow")
    table.add_row("Status", str(res.status))
    table.add_row("Cavitation Index (sigma)", f"{res.cavitation_number_sigma} (Threshold >= 0.85)")
    table.add_row("Cavitation Detected", str(res.cavitation_inception_detected))
    table.add_row("Recommended Pitch", f"{res.recommended_pitch_deg} deg")
    table.add_row("Grate Clogged", str(res.grate_clogged))
    console.print(table)
