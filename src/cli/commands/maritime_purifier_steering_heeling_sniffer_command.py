"""Typer CLI commands for Maritime Phases 383-386.

Bilingual commands (EN/VN) for Fuel Purifier, Emergency Steering,
Anti-Heeling Ballast Control, and Tanker Pump Room Gas Sniffer.
"""

from rich.console import Console
from rich.table import Table
import typer

from src.core.maritime.phase_383_marine_fuel_purifier_clarifier import (
    FuelPurifierInput,
    MarineFuelPurifierEngine,
)
from src.core.maritime.phase_384_auxiliary_emergency_steering import (
    AuxiliaryEmergencySteeringEngine,
    SteeringGearInput,
)
from src.core.maritime.phase_385_anti_heeling_ballast_pumping import (
    AntiHeelingBallastEngine,
    AntiHeelingInput,
)
from src.core.maritime.phase_386_tanker_pumproom_gas_sniffer import (
    PumpRoomGasInput,
    TankerPumpRoomGasEngine,
)

console = Console()
purifier_app = typer.Typer(name="purifier", help="Marine Centrifugal Fuel Oil Purifier & Clarifier (ISO 8217)")
steering_app = typer.Typer(name="emergsteering", help="Auxiliary Emergency Steering Gear (SOLAS II-1 Reg 29/30)")
heeling_app = typer.Typer(name="antiheeling", help="Automatic Anti-Heeling Ballast Pumping (IMO MSC.267(85))")
gas_app = typer.Typer(name="pumproomgas", help="Tanker Pump Room Gas & Bilge Sniffer (SOLAS II-2 Reg 4.5.10)")


@purifier_app.command("evaluate")
def evaluate_purifier(
    fuel_type: str = typer.Option("HFO", "--fuel", "-f", help="Fuel type (HFO, VLSFO, MGO)"),
    flow_rate: float = typer.Option(3.5, "--flow", help="Flow rate in m3/h"),
    rpm: float = typer.Option(8500.0, "--rpm", help="Centrifuge bowl RPM"),
    temp_c: float = typer.Option(98.0, "--temp", help="Fuel inlet temperature C"),
    cat_fines: float = typer.Option(45.0, "--cat-fines", help="Inlet Al+Si cat fines in ppm"),
    vibration: float = typer.Option(3.8, "--vib", help="Bowl vibration velocity RMS mm/s"),
) -> None:
    """Evaluate marine fuel centrifuge purification and cat fines removal."""
    engine = MarineFuelPurifierEngine()
    inp = FuelPurifierInput(
        fuel_type=fuel_type,
        flow_rate_m3_h=flow_rate,
        bowl_speed_rpm=rpm,
        inlet_temp_c=temp_c,
        cat_fines_inlet_ppm=cat_fines,
        vibration_velocity_rms_mm_s=vibration,
    )
    res = engine.evaluate(inp)

    table = Table(title="[bold cyan]Marine Fuel Oil Purifier & Clarifier Evaluation[/bold cyan]")
    table.add_column("Parameter", style="green")
    table.add_column("Value", style="yellow")
    table.add_row("Centrifugal G-Force", f"{res.g_force_factor} g")
    table.add_row("Separation Efficiency", f"{res.separation_efficiency_pct}%")
    table.add_row("Outlet Cat Fines (Al+Si)", f"{res.cat_fines_outlet_ppm} ppm")
    table.add_row("Vibration Status", res.vibration_status)
    table.add_row("Purifier Status", res.purifier_status)
    table.add_row("De-sludge Required", str(res.desludge_required))
    table.add_row("Feed Valve Open", str(res.feed_valve_open))
    console.print(table)
    if res.warnings:
        console.print("[bold red]Warnings / Alerts:[/bold red]")
        for w in res.warnings:
            console.print(f"  • {w}")


@steering_app.command("evaluate")
def evaluate_steering(
    mode: str = typer.Option("MAIN", "--mode", "-m", help="Steering mode (MAIN, AUXILIARY_EMERGENCY)"),
    elapsed_time: float = typer.Option(24.5, "--time", "-t", help="Rudder swing travel time in seconds"),
    pressure: float = typer.Option(195.0, "--pressure", "-p", help="Hydraulic system pressure in bar"),
    oil_level: float = typer.Option(78.0, "--oil", help="Expansion tank oil level percentage"),
    emergency_power: bool = typer.Option(False, "--emerg-power", help="Is emergency power feed active"),
) -> None:
    """Evaluate steering gear statutory travel times and hydraulic compliance."""
    engine = AuxiliaryEmergencySteeringEngine()
    inp = SteeringGearInput(
        mode=mode,
        elapsed_time_s=elapsed_time,
        hydraulic_pressure_bar=pressure,
        oil_tank_level_pct=oil_level,
        emergency_power_active=emergency_power,
    )
    res = engine.evaluate(inp)

    table = Table(title="[bold cyan]Auxiliary Emergency Steering Gear Compliance[/bold cyan]")
    table.add_column("Check", style="green")
    table.add_column("Status / Value", style="yellow")
    table.add_row("Operating Mode", res.mode)
    table.add_row("Travel Time / Limit", f"{res.travel_time_s}s / {res.time_limit_s}s")
    table.add_row("Travel Time Compliant", str(res.travel_compliant))
    table.add_row("Hydraulic Integrity", res.hydraulic_integrity)
    table.add_row("Overall Steering Status", res.steering_status)
    console.print(table)
    if res.warnings:
        console.print("[bold red]Warnings / Alerts:[/bold red]")
        for w in res.warnings:
            console.print(f"  • {w}")


@heeling_app.command("evaluate")
def evaluate_anti_heeling(
    heel_deg: float = typer.Option(0.8, "--heel", help="Current vessel heel angle in degrees (+ stbd, - port)"),
    heel_rate: float = typer.Option(0.05, "--rate", help="Heeling rate d(theta)/dt in deg/s"),
    displacement: float = typer.Option(85000.0, "--disp", help="Vessel displacement in metric tonnes"),
    gm: float = typer.Option(1.85, "--gm", help="Transverse metacentric height GM_T in meters"),
) -> None:
    """Evaluate container vessel anti-heeling ballast balance and counter-flooding."""
    engine = AntiHeelingBallastEngine()
    inp = AntiHeelingInput(
        current_heel_deg=heel_deg,
        heel_rate_deg_s=heel_rate,
        displacement_tonnes=displacement,
        gm_transverse_m=gm,
    )
    res = engine.evaluate(inp)

    table = Table(title="[bold cyan]Automatic Anti-Heeling Ballast Control[/bold cyan]")
    table.add_column("Parameter", style="green")
    table.add_column("Evaluation", style="yellow")
    table.add_row("Restoring Moment", f"{res.restoring_moment_kn_m:,.1f} kN.m")
    table.add_row("Operational Status", res.operational_status)
    table.add_row("Target Pump Action", res.target_pump_action)
    table.add_row("Rapid Trigger Active", str(res.rapid_response_triggered))
    table.add_row("Flow Demand", f"{res.pump_flow_demand_m3_h} m3/h")
    console.print(table)
    if res.warnings:
        console.print("[bold red]Warnings / Alerts:[/bold red]")
        for w in res.warnings:
            console.print(f"  • {w}")


@gas_app.command("evaluate")
def evaluate_pumproom_gas(
    lel_pct: float = typer.Option(4.5, "--lel", help="Hydrocarbon gas concentration in % LEL"),
    h2s_ppm: float = typer.Option(1.0, "--h2s", help="Hydrogen sulfide concentration in ppm"),
    o2_pct: float = typer.Option(20.9, "--o2", help="Oxygen concentration in %"),
    ach: float = typer.Option(22.0, "--ach", help="Ventilation air changes per hour"),
    bilge_m: float = typer.Option(0.12, "--bilge", help="Bilge well water level in meters"),
) -> None:
    """Evaluate tanker pump room atmosphere, gas sniffer, and interlocks."""
    engine = TankerPumpRoomGasEngine()
    inp = PumpRoomGasInput(
        hydrocarbon_lel_pct=lel_pct,
        h2s_concentration_ppm=h2s_ppm,
        oxygen_concentration_pct=o2_pct,
        ventilation_ach=ach,
        bilge_water_level_m=bilge_m,
    )
    res = engine.evaluate(inp)

    table = Table(title="[bold cyan]Tanker Pump Room Gas & Bilge Safety Evaluation[/bold cyan]")
    table.add_column("Parameter", style="green")
    table.add_column("Result", style="yellow")
    table.add_row("Atmosphere Status", res.atmosphere_status)
    table.add_row("Ventilation Compliant", str(res.ventilation_compliant))
    table.add_row("Cargo Pump Trip Required", str(res.cargo_pump_trip_required))
    table.add_row("Bilge Flood Alarm", str(res.bilge_alarm))
    table.add_row("Safe Entry Permitted", str(res.entry_permitted))
    console.print(table)
    if res.warnings:
        console.print("[bold red]Warnings / Alerts:[/bold red]")
        for w in res.warnings:
            console.print(f"  • {w}")
