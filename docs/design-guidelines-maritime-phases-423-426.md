# Design Guidelines: Maritime Phases 423–426

## 1. Ergonomics & CLI Nomenclature
- Command group prefixes:
  - Phase 423: `sootwash` / `ruasuoithan`
  - Phase 424: `thermaloil` / `dautainhiet`
  - Phase 425: `bilgeevap` / `bochoilagong`
  - Phase 426: `crankcaseomd` / `suongdaucarte`
- Multi-lingual output: English status alongside clear Vietnamese explanations for engineering crew.
- High-contrast terminal formatting:
  - ANSI Green for Nominal operation.
  - ANSI Yellow for Pre-alarm warnings (e.g., differential pressure rising, $C_{\text{mist}} \ge 1.0\,\text{mg/L}$).
  - ANSI Red for Emergency Trips (e.g., $T_{\text{exh}} \ge 380^\circ\text{C}$, $C_{\text{mist}} \ge 2.0\,\text{mg/L}$).

## 2. Safety Interlock State Machine
Each engine exposes:
1. `evaluate(...)` returning a strongly-typed assessment dataclass.
2. `trip_active: bool` indicating immediate equipment shutdown.
3. `warnings: List[str]` containing specific physical or regulatory violations.
4. `interlock_clear: bool` validating safe permit-to-work or operating window.
