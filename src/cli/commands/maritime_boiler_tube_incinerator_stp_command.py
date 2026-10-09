"""Typer CLI commands for Maritime Phases 403-406.

Includes Marine Boiler Water Chemistry, Stern Tube Lubrication,
Marine Incinerator Sludge Destruction, and Sewage Treatment Plant MBR.
Strictly < 180 LOC, zero mocks.
"""

import typer
from rich.console import Console
from rich.table import Table

from src.core.maritime.phase_403_boiler_water_chemistry import (
    BoilerWaterEngine,
    BoilerWaterInput,
)
from src.core.maritime.phase_404_stern_tube_eal import (
    SternTubeEngine,
    SternTubeInput,
)
from src.core.maritime.phase_405_incinerator_sludge import (
    SludgeIncineratorEngine,
    SludgeIncineratorInput,
)
from src.core.maritime.phase_406_sewage_treatment_mbr import (
    SewageTreatmentEngine,
    SewageTreatmentInput,
)

console = Console()

boiler_app = typer.Typer(help="Phase 403: Marine Boiler Water Chemistry & Deaeration (BS 2486 / ASME Sec VII)")
sterntube_app = typer.Typer(help="Phase 404: Stern Tube Lubrication & Bio-Lubricant Seal Water Ingress (US EPA VGP)")
incinerator_app = typer.Typer(help="Phase 405: Marine Incinerator Sludge Oil Destruction (IMO MEPC.76(40))")
sewage_app = typer.Typer(help="Phase 406: Marine Sewage Treatment Plant MBR & Nutrient Removal (IMO MEPC.227(64))")


@boiler_app.callback(invoke_without_command=True)
def evaluate_boiler(
    o2_ppm: float = typer.Option(0.005, "--o2-ppm", help="Dissolved oxygen in feedwater (ppm)"),
    hydrazine_ppm: float = typer.Option(0.05, "--hydrazine-ppm", help="Hydrazine residual (ppm)"),
    ph: float = typer.Option(10.0, "--ph", help="Boiler water coordinated pH"),
    po4_ppm: float = typer.Option(25.0, "--po4-ppm", help="Phosphate PO4 buffer (ppm)"),
    cond_us: float = typer.Option(450.0, "--cond-us", help="Conductivity (uS/cm)"),
    tds_ppm: float = typer.Option(600.0, "--tds-ppm", help="Total dissolved solids (ppm)"),
    deaerator_temp: float = typer.Option(104.5, "--deaerator-temp", help="Deaerator temperature (°C)"),
):
    """Evaluate boiler feedwater chemistry, phosphate buffer, and blowdown requirements."""
    inp = BoilerWaterInput(
        dissolved_oxygen_ppm=o2_ppm,
        hydrazine_residual_ppm=hydrazine_ppm,
        boiler_ph=ph,
        phosphate_po4_ppm=po4_ppm,
        conductivity_us_cm=cond_us,
        tds_ppm=tds_ppm,
        deaerator_temp_c=deaerator_temp,
    )
    res = BoilerWaterEngine().evaluate(inp)

    table = Table(title="Maritime Phase 403: Boiler Water Chemistry (BS 2486)")
    table.add_column("Metric", style="cyan")
    table.add_column("Status / Evaluation", style="magenta")
    table.add_row("Overall Status", res.status.value)
    table.add_row("O2 Scavenging Pass", "YES" if res.oxygen_scavenging_pass else "NO")
    table.add_row("Phosphate Buffer Pass", "YES" if res.phosphate_buffer_pass else "NO")
    table.add_row("Deaeration Efficient", "YES" if res.deaeration_efficient else "NO")
    table.add_row("Blowdown Recommended", "YES" if res.blowdown_recommended else "NO")
    table.add_row("Magnetite Passivation", "STABLE" if res.magnetite_passivation_stable else "AT RISK")
    console.print(table)


@sterntube_app.callback(invoke_without_command=True)
def evaluate_stern_tube(
    header_bar: float = typer.Option(0.55, "--header-bar", help="Lube header tank pressure (bar)"),
    draft_bar: float = typer.Option(0.32, "--draft-bar", help="Seawater draft pressure (bar)"),
    water_ppm: float = typer.Option(350.0, "--water-ppm", help="Water content in oil (ppm)"),
    visc_cst: float = typer.Option(68.0, "--visc-cst", help="Measured oil viscosity at 40°C (cSt)"),
    nom_visc: float = typer.Option(68.0, "--nom-visc", help="Nominal oil viscosity rating (cSt)"),
    bearing_temp: float = typer.Option(52.0, "--bearing-temp", help="Aft bearing temperature (°C)"),
    level_pct: float = typer.Option(85.0, "--level-pct", help="Gravity tank level (%)"),
):
    """Evaluate stern tube differential seal pressure, EAL water ingress, and bearing temperature."""
    inp = SternTubeInput(
        lube_header_pressure_bar=header_bar,
        seawater_draft_pressure_bar=draft_bar,
        water_content_ppm=water_ppm,
        viscosity_cst_40c=visc_cst,
        nominal_viscosity_cst=nom_visc,
        aft_bearing_temp_c=bearing_temp,
        header_tank_level_pct=level_pct,
    )
    res = SternTubeEngine().evaluate(inp)

    table = Table(title="Maritime Phase 404: Stern Tube Lubrication & EAL (US EPA VGP)")
    table.add_column("Metric", style="cyan")
    table.add_column("Status / Evaluation", style="magenta")
    table.add_row("Overall Status", res.status.value)
    table.add_row("Seal Barrier Intact", "YES" if res.seal_barrier_intact else "NO")
    table.add_row("Differential Pressure", f"{res.pressure_diff_bar} bar")
    table.add_row("EAL Water Ingress OK", "YES" if res.eal_water_compliant else "NO")
    table.add_row("EAL Viscosity OK", "YES" if res.eal_viscosity_compliant else "NO")
    table.add_row("Bearing Thermal Safe", "YES" if res.bearing_thermal_safe else "NO")
    console.print(table)


@incinerator_app.callback(invoke_without_command=True)
def evaluate_incinerator(
    chamber_temp: float = typer.Option(920.0, "--chamber-temp", help="Combustion chamber temp (°C)"),
    flue_temp: float = typer.Option(280.0, "--flue-temp", help="Flue gas exit temp (°C)"),
    visc_cst: float = typer.Option(12.5, "--visc-cst", help="Sludge viscosity at nozzle (cSt)"),
    draft_mmwc: float = typer.Option(-15.0, "--draft-mmwc", help="Furnace draft pressure (mmWC)"),
    in_port: bool = typer.Option(False, "--in-port", help="Vessel is inside port/estuary limits"),
):
    """Evaluate shipboard sludge incinerator combustion temperature, nozzle viscosity, and port interlocks."""
    inp = SludgeIncineratorInput(
        combustion_chamber_temp_c=chamber_temp,
        flue_gas_exit_temp_c=flue_temp,
        sludge_viscosity_cst=visc_cst,
        furnace_draft_pressure_mmwc=draft_mmwc,
        in_port_or_estuary=in_port,
    )
    res = SludgeIncineratorEngine().evaluate(inp)

    table = Table(title="Maritime Phase 405: Sludge Incinerator (IMO MEPC.76(40))")
    table.add_column("Metric", style="cyan")
    table.add_column("Status / Evaluation", style="magenta")
    table.add_row("Overall Status", res.status.value)
    table.add_row("Sludge Feed Permitted", "YES" if res.sludge_feed_permitted else "NO")
    table.add_row("Chamber Temperature OK", "YES" if res.temperature_compliant else "NO")
    table.add_row("Atomization Viscosity OK", "YES" if res.atomization_compliant else "NO")
    table.add_row("Furnace Draft OK", "YES" if res.flue_draft_compliant else "NO")
    console.print(table)


@sewage_app.callback(invoke_without_command=True)
def evaluate_sewage(
    bod5: float = typer.Option(12.0, "--bod5", help="Biochemical Oxygen Demand (mg/L)"),
    cod: float = typer.Option(85.0, "--cod", help="Chemical Oxygen Demand (mg/L)"),
    tss: float = typer.Option(15.0, "--tss", help="Total Suspended Solids (mg/L)"),
    coliform: float = typer.Option(40.0, "--coliform", help="Thermotolerant Coliforms (CFU/100mL)"),
    tn: float = typer.Option(14.0, "--tn", help="Total Nitrogen (mg/L)"),
    tp: float = typer.Option(0.7, "--tp", help="Total Phosphorus (mg/L)"),
    tmp_bar: float = typer.Option(0.18, "--tmp-bar", help="MBR Transmembrane Pressure (bar)"),
    special_area: bool = typer.Option(True, "--special-area", help="Operating in Special Area (e.g. Baltic)"),
):
    """Evaluate sewage treatment plant effluent quality, Special Area nutrient removal, and MBR TMP."""
    inp = SewageTreatmentInput(
        bod5_mg_l=bod5,
        cod_mg_l=cod,
        tss_mg_l=tss,
        coliform_cfu_100ml=coliform,
        total_nitrogen_mg_l=tn,
        total_phosphorus_mg_l=tp,
        transmembrane_pressure_bar=tmp_bar,
        operating_in_special_area=special_area,
    )
    res = SewageTreatmentEngine().evaluate(inp)

    table = Table(title="Maritime Phase 406: STP MBR & Nutrient Removal (IMO MEPC.227(64))")
    table.add_column("Metric", style="cyan")
    table.add_column("Status / Evaluation", style="magenta")
    table.add_row("Overall Status", res.status.value)
    table.add_row("Overboard Discharge Permitted", "YES" if res.overboard_discharge_permitted else "NO")
    table.add_row("Standard Effluent Pass", "YES" if res.standard_effluent_pass else "NO")
    table.add_row("Nutrient Removal Pass", "YES" if res.nutrient_removal_pass else "NO")
    table.add_row("Membrane Safe", "YES" if res.membrane_fouling_safe else "NO")
    console.print(table)
