"""Batch registration for .claude/commands/ slash commands.
Each slash command maps to a mekong-cli subcommand invocation.
Registered onto the root Typer app via register_slash_commands().
"""

import os
import subprocess
import typer
import shlex


def _dispatch_mekong(subcommand: str, args: str) -> None:
    """Dispatch to mekong subcommand via python3 -m src.main."""
    cmd = ["python3", "-m", "src.main", subcommand]
    if args:
        cmd.extend(shlex.split(args))
    result = subprocess.run(
        cmd,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    raise typer.Exit(code=result.returncode)



def register_slash_commands(app: typer.Typer) -> None:
    """Register all .claude/commands/ slash commands."""

    @app.command(name="4-project")
    def cmd_4_project(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """4-project: slash command → mekong 4-project"""
        _dispatch_mekong("4-project", args)

    @app.command(name="accounting-daily")
    def accounting_daily(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """accounting-daily: slash command → mekong accounting-daily"""
        _dispatch_mekong("accounting-daily", args)

    @app.command(name="accounting-invoice-batch")
    def accounting_invoice_batch(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """accounting-invoice-batch: slash command → mekong accounting-invoice-batch"""
        _dispatch_mekong("accounting-invoice-batch", args)

    @app.command(name="ae-close-report")
    def ae_close_report(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """ae-close-report: slash command → mekong ae-close-report"""
        _dispatch_mekong("ae-close-report", args)

    @app.command(name="ae-deal-prep")
    def ae_deal_prep(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """ae-deal-prep: slash command → mekong ae-deal-prep"""
        _dispatch_mekong("ae-deal-prep", args)

    @app.command(name="ae-follow-up")
    def ae_follow_up(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """ae-follow-up: slash command → mekong ae-follow-up"""
        _dispatch_mekong("ae-follow-up", args)

    @app.command(name="ae-outreach")
    def ae_outreach(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """ae-outreach: slash command → mekong ae-outreach"""
        _dispatch_mekong("ae-outreach", args)

    @app.command(name="agy")
    def agy(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """agy: slash command → mekong agy"""
        _dispatch_mekong("agy", args)

    @app.command(name="ai-artist")
    def ai_artist(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """ai-artist: slash command → mekong ai-artist"""
        _dispatch_mekong("ai-artist", args)

    @app.command(name="ai-multimodal")
    def ai_multimodal(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """ai-multimodal: slash command → mekong ai-multimodal"""
        _dispatch_mekong("ai-multimodal", args)

    @app.command(name="algo-status")
    def algo_status(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """algo-status: slash command → mekong algo-status"""
        _dispatch_mekong("algo-status", args)

    @app.command(name="analyst-forecast-update")
    def analyst_forecast_update(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """analyst-forecast-update: slash command → mekong analyst-forecast-update"""
        _dispatch_mekong("analyst-forecast-update", args)

    @app.command(name="analyst-report")
    def analyst_report(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """analyst-report: slash command → mekong analyst-report"""
        _dispatch_mekong("analyst-report", args)

    @app.command(name="antibridge")
    def antibridge(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """antibridge: slash command → mekong antibridge"""
        _dispatch_mekong("antibridge", args)

    @app.command(name="approve")
    def approve(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """approve: slash command → mekong approve"""
        _dispatch_mekong("approve", args)

    @app.command(name="ask")
    def ask(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """ask: slash command → mekong ask"""
        _dispatch_mekong("ask", args)

    @app.command(name="audit-compliance")
    def audit_compliance(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """audit-compliance: slash command → mekong audit-compliance"""
        _dispatch_mekong("audit-compliance", args)

    @app.command(name="audit-execute")
    def audit_execute(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """audit-execute: slash command → mekong audit-execute"""
        _dispatch_mekong("audit-execute", args)

    @app.command(name="audit-itgc")
    def audit_itgc(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """audit-itgc: slash command → mekong audit-itgc"""
        _dispatch_mekong("audit-itgc", args)

    @app.command(name="audit-plan")
    def audit_plan(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """audit-plan: slash command → mekong audit-plan"""
        _dispatch_mekong("audit-plan", args)

    @app.command(name="audit-report")
    def audit_report(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """audit-report: slash command → mekong audit-report"""
        _dispatch_mekong("audit-report", args)

    @app.command(name="audit-sox")
    def audit_sox(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """audit-sox: slash command → mekong audit-sox"""
        _dispatch_mekong("audit-sox", args)

    @app.command(name="audit-trail")
    def audit_trail(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """audit-trail: slash command → mekong audit-trail"""
        _dispatch_mekong("audit-trail", args)

    @app.command(name="backend-api-build")
    def backend_api_build(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """backend-api-build: slash command → mekong backend-api-build"""
        _dispatch_mekong("backend-api-build", args)

    @app.command(name="backend-db-task")
    def backend_db_task(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """backend-db-task: slash command → mekong backend-db-task"""
        _dispatch_mekong("backend-db-task", args)

    @app.command(name="bhxh")
    def bhxh(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """bhxh: slash command → mekong bhxh"""
        _dispatch_mekong("bhxh", args)

    @app.command(name="binh-phap")
    def binh_phap(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """binh-phap: slash command → mekong binh-phap"""
        _dispatch_mekong("binh-phap", args)

    @app.command(name="board-compliance")
    def board_compliance(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """board-compliance: slash command → mekong board-compliance"""
        _dispatch_mekong("board-compliance", args)

    @app.command(name="board-manage")
    def board_manage(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """board-manage: slash command → mekong board-manage"""
        _dispatch_mekong("board-manage", args)

    @app.command(name="board-minutes")
    def board_minutes(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """board-minutes: slash command → mekong board-minutes"""
        _dispatch_mekong("board-minutes", args)

    @app.command(name="board-report")
    def board_report(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """board-report: slash command → mekong board-report"""
        _dispatch_mekong("board-report", args)

    @app.command(name="bootstrap-auto")
    def bootstrap_auto(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """bootstrap-auto: slash command → mekong bootstrap-auto"""
        _dispatch_mekong("bootstrap-auto", args)

    @app.command(name="bootstrap-auto-fast")
    def bootstrap_auto_fast(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """bootstrap-auto-fast: slash command → mekong bootstrap-auto-fast"""
        _dispatch_mekong("bootstrap-auto-fast", args)

    @app.command(name="bootstrap-auto-parallel")
    def bootstrap_auto_parallel(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """bootstrap-auto-parallel: slash command → mekong bootstrap-auto-parallel"""
        _dispatch_mekong("bootstrap-auto-parallel", args)

    @app.command(name="brain-evolution-log")
    def brain_evolution_log(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """brain-evolution-log: slash command → mekong brain-evolution-log"""
        _dispatch_mekong("brain-evolution-log", args)

    @app.command(name="bridge")
    def bridge(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """bridge: slash command → mekong bridge"""
        _dispatch_mekong("bridge", args)

    @app.command(name="business-campaign-launch")
    def business_campaign_launch(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """business-campaign-launch: slash command → mekong business-campaign-launch"""
        _dispatch_mekong("business-campaign-launch", args)

    @app.command(name="business-client-onboard")
    def business_client_onboard(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """business-client-onboard: slash command → mekong business-client-onboard"""
        _dispatch_mekong("business-client-onboard", args)

    @app.command(name="business-financial-close")
    def business_financial_close(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """business-financial-close: slash command → mekong business-financial-close"""
        _dispatch_mekong("business-financial-close", args)

    @app.command(name="business-hiring-sprint")
    def business_hiring_sprint(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """business-hiring-sprint: slash command → mekong business-hiring-sprint"""
        _dispatch_mekong("business-hiring-sprint", args)

    @app.command(name="business-quarterly-review")
    def business_quarterly_review(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """business-quarterly-review: slash command → mekong business-quarterly-review"""
        _dispatch_mekong("business-quarterly-review", args)

    @app.command(name="business-report")
    def business_report(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """business-report: slash command → mekong business-report"""
        _dispatch_mekong("business-report", args)

    @app.command(name="business-revenue-engine")
    def business_revenue_engine(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """business-revenue-engine: slash command → mekong business-revenue-engine"""
        _dispatch_mekong("business-revenue-engine", args)

    @app.command(name="cc-cli-input-rules")
    def cc_cli_input_rules(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """cc-cli-input-rules: slash command → mekong cc-cli-input-rules"""
        _dispatch_mekong("cc-cli-input-rules", args)

    @app.command(name="cdp-identity")
    def cdp_identity(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """cdp-identity: slash command → mekong cdp-identity"""
        _dispatch_mekong("cdp-identity", args)

    @app.command(name="cdp-journey")
    def cdp_journey(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """cdp-journey: slash command → mekong cdp-journey"""
        _dispatch_mekong("cdp-journey", args)

    @app.command(name="cdp-profile")
    def cdp_profile(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """cdp-profile: slash command → mekong cdp-profile"""
        _dispatch_mekong("cdp-profile", args)

    @app.command(name="cdp-segment")
    def cdp_segment(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """cdp-segment: slash command → mekong cdp-segment"""
        _dispatch_mekong("cdp-segment", args)

    @app.command(name="chrome-profile")
    def chrome_profile(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """chrome-profile: slash command → mekong chrome-profile"""
        _dispatch_mekong("chrome-profile", args)

    @app.command(name="ci-ci-status")
    def ci_ci_status(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """ci-ci-status: slash command → mekong ci-ci-status"""
        _dispatch_mekong("ci-ci-status", args)

    @app.command(name="ci-debugger")
    def ci_debugger(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """ci-debugger: slash command → mekong ci-debugger"""
        _dispatch_mekong("ci-debugger", args)

    @app.command(name="ci-deploy")
    def ci_deploy(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """ci-deploy: slash command → mekong ci-deploy"""
        _dispatch_mekong("ci-deploy", args)

    @app.command(name="ci-run-ci")
    def ci_run_ci(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """ci-run-ci: slash command → mekong ci-run-ci"""
        _dispatch_mekong("ci-run-ci", args)

    @app.command(name="coding-level")
    def coding_level(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """coding-level: slash command → mekong coding-level"""
        _dispatch_mekong("coding-level", args)

    @app.command(name="context-engineering")
    def context_engineering(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """context-engineering: slash command → mekong context-engineering"""
        _dispatch_mekong("context-engineering", args)

    @app.command(name="cook")
    def cook(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """cook: slash command → mekong cook"""
        _dispatch_mekong("cook", args)

    @app.command(name="cook-auto")
    def cook_auto(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """cook-auto: slash command → mekong cook-auto"""
        _dispatch_mekong("cook-auto", args)

    @app.command(name="cook-auto-parallel")
    def cook_auto_parallel(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """cook-auto-parallel: slash command → mekong cook-auto-parallel"""
        _dispatch_mekong("cook-auto-parallel", args)

    @app.command(name="copywriting")
    def copywriting(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """copywriting: slash command → mekong copywriting"""
        _dispatch_mekong("copywriting", args)

    @app.command(name="cti-expert")
    def cti_expert(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """cti-expert: slash command → mekong cti-expert"""
        _dispatch_mekong("cti-expert", args)

    @app.command(name="docs-seeker")
    def docs_seeker(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """docs-seeker: slash command → mekong docs-seeker"""
        _dispatch_mekong("docs-seeker", args)

    @app.command(name="docx")
    def docx(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """docx: slash command → mekong docx"""
        _dispatch_mekong("docx", args)

    @app.command(name="fix")
    def fix(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """fix: slash command → mekong fix"""
        _dispatch_mekong("fix", args)

    @app.command(name="frontend-design")
    def frontend_design(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """frontend-design: slash command → mekong frontend-design"""
        _dispatch_mekong("frontend-design", args)

    @app.command(name="graphify")
    def graphify(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """graphify: slash command → mekong graphify"""
        _dispatch_mekong("graphify", args)

    @app.command(name="markdown-novel-viewer")
    def markdown_novel_viewer(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """markdown-novel-viewer: slash command → mekong markdown-novel-viewer"""
        _dispatch_mekong("markdown-novel-viewer", args)

    @app.command(name="mekong")
    def mekong(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """mekong: slash command → mekong mekong"""
        if not args:
            typer.echo("Usage: mekong <subcommand> [args...]")
            raise typer.Exit(0)
        cmd = ["python3", "-m", "src.main"] + args.split()
        result = subprocess.run(cmd)
        raise typer.Exit(code=result.returncode)

    @app.command(name="pdf")
    def pdf(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """pdf: slash command → mekong pdf"""
        _dispatch_mekong("pdf", args)

    @app.command(name="plan")
    def plan(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """plan: slash command → mekong plan"""
        _dispatch_mekong("plan", args)

    @app.command(name="plans-kanban")
    def plans_kanban(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """plans-kanban: slash command → mekong plans-kanban"""
        _dispatch_mekong("plans-kanban", args)

    @app.command(name="pptx")
    def pptx(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """pptx: slash command → mekong pptx"""
        _dispatch_mekong("pptx", args)

    @app.command(name="preview")
    def preview(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """preview: slash command → mekong preview"""
        _dispatch_mekong("preview", args)

    @app.command(name="research")
    def research(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """research: slash command → mekong research"""
        _dispatch_mekong("research", args)

    @app.command(name="revenue")
    def revenue(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """revenue: slash command → mekong revenue"""
        _dispatch_mekong("revenue", args)

    @app.command(name="scenario")
    def scenario(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """scenario: slash command → mekong scenario"""
        _dispatch_mekong("scenario", args)

    @app.command(name="scout")
    def scout(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """scout: slash command → mekong scout"""
        _dispatch_mekong("scout", args)

    @app.command(name="sequential-thinking")
    def sequential_thinking(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """sequential-thinking: slash command → mekong sequential-thinking"""
        _dispatch_mekong("sequential-thinking", args)

    @app.command(name="show-off")
    def show_off(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """show-off: slash command → mekong show-off"""
        _dispatch_mekong("show-off", args)

    @app.command(name="skill-creator")
    def skill_creator(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """skill-creator: slash command → mekong skill-creator"""
        _dispatch_mekong("skill-creator", args)

    @app.command(name="stitch")
    def stitch(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """stitch: slash command → mekong stitch"""
        _dispatch_mekong("stitch", args)

    @app.command(name="sync")
    def sync(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """sync: slash command → mekong sync"""
        _dispatch_mekong("sync", args)

    @app.command(name="tasks")
    def tasks(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """tasks: slash command → mekong tasks"""
        _dispatch_mekong("tasks", args)

    @app.command(name="team")
    def team(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """team: slash command → mekong team"""
        _dispatch_mekong("team", args)

    @app.command(name="tech-graph")
    def tech_graph(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """tech-graph: slash command → mekong tech-graph"""
        _dispatch_mekong("tech-graph", args)

    @app.command(name="threejs")
    def threejs(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """threejs: slash command → mekong threejs"""
        _dispatch_mekong("threejs", args)

    @app.command(name="ui-check")
    def ui_check(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """ui-check: slash command → mekong ui-check"""
        _dispatch_mekong("ui-check", args)

    @app.command(name="ui-ux-pro-max")
    def ui_ux_pro_max(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """ui-ux-pro-max: slash command → mekong ui-ux-pro-max"""
        _dispatch_mekong("ui-ux-pro-max", args)

    @app.command(name="use-mcp")
    def use_mcp(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """use-mcp: slash command → mekong use-mcp"""
        _dispatch_mekong("use-mcp", args)

    @app.command(name="watzup")
    def watzup(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """watzup: slash command → mekong watzup"""
        _dispatch_mekong("watzup", args)

    @app.command(name="worktree")
    def worktree(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """worktree: slash command → mekong worktree"""
        _dispatch_mekong("worktree", args)

    @app.command(name="xlsx")
    def xlsx(
        args: str = typer.Argument(default="", help="Arguments to pass through"),
    ) -> None:
        """xlsx: slash command → mekong xlsx"""
        _dispatch_mekong("xlsx", args)

