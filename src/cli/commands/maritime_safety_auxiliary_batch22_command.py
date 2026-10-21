import typer
from rich.console import Console

from src.core.maritime.phase_547_fgss_glycol_vaporizer_gvu_interlock import (
    FgssGlycolGvuTelemetry,
    FgssGlycolVaporizerGvuEngine,
)
from src.core.maritime.phase_548_charge_air_cooler_condensate_interlock import (
    ChargeAirCondensateTelemetry,
    ChargeAirCoolerCondensateEngine,
)
from src.core.maritime.phase_549_high_expansion_foam_generator_interlock import (
    HighExpansionFoamGeneratorEngine,
    HighExpFoamGeneratorTelemetry,
)
from src.core.maritime.phase_550_dp_bus_tie_wcsf_redundancy_interlock import (
    DpBusTieRedundancyTelemetry,
    DpBusTieWcsfRedundancyEngine,
)

maritime_aux22_app = typer.Typer(help="Maritime Auxiliary Automation Batch 22 (Phases 547-550)")
console = Console()


@maritime_aux22_app.command("fgss-check")
def fgss_check(
    gas_temp: float = 35.0,
    gvu_lel: float = 0.0,
    gvu_ach: float = 36.0,
    glycol_temp: float = 45.0,
) -> None:
    res = FgssGlycolVaporizerGvuEngine.evaluate(
        FgssGlycolGvuTelemetry(gas_temp, gvu_lel, gvu_ach, glycol_temp)
    )
    console.print(f"[bold cyan]Phase 547 FGSS GVU:[/bold cyan] {res.state.value} ({res.interlock_code})")


@maritime_aux22_app.command("cac-check")
def cac_check(
    catcher_pct: float = 22.0,
    salinity_ppm: float = 15.0,
    dp_kpa: float = 2.1,
) -> None:
    res = ChargeAirCoolerCondensateEngine.evaluate(
        ChargeAirCondensateTelemetry(catcher_pct, salinity_ppm, dp_kpa)
    )
    console.print(f"[bold cyan]Phase 548 CAC Condensate:[/bold cyan] {res.state.value} ({res.interlock_code})")


@maritime_aux22_app.command("highexpfoam-check")
def highexpfoam_check(
    manifold_bar: float = 6.8,
    conc_pct: float = 2.1,
    backpressure_pa: float = 65.0,
    dampers_closed: bool = True,
) -> None:
    res = HighExpansionFoamGeneratorEngine.evaluate(
        HighExpFoamGeneratorTelemetry(manifold_bar, conc_pct, backpressure_pa, dampers_closed)
    )
    console.print(f"[bold cyan]Phase 549 High-Exp Foam:[/bold cyan] {res.state.value} ({res.interlock_code})")


@maritime_aux22_app.command("dpbustie-check")
def dpbustie_check(
    volt_pct: float = 99.5,
    freq_dev: float = 0.1,
    wcsf_load: float = 68.0,
    margin_pct: float = 35.0,
) -> None:
    res = DpBusTieWcsfRedundancyEngine.evaluate(
        DpBusTieRedundancyTelemetry(volt_pct, freq_dev, wcsf_load, margin_pct)
    )
    console.print(f"[bold cyan]Phase 550 DP Bus-Tie:[/bold cyan] {res.state.value} ({res.interlock_code})")
