# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

# Mekong CLI - Core Module
# Lazy imports — modules loaded on first access, not at import time.

def __getattr__(name: str):
    """Lazy import core modules on first access."""
    _imports = {
        "AgentBase": ".agent_base",
        "Result": ".agent_base",
        "Task": ".agent_base",
        "TaskStatus": ".agent_base",
        "AgentRegistry": ".agent_registry",
        "Alert": ".alert_router",
        "AlertConfig": ".alert_router",
        "AlertRouter": ".alert_router",
        "AlertSeverity": ".alert_router",
        "get_alert_router": ".alert_router",
        "DAGScheduler": ".dag_scheduler",
        "DAGStepResult": ".dag_scheduler",
        "validate_dag": ".dag_scheduler",
        "RecipeExecutor": ".executor",
        "OrchestrationResult": ".orchestrator",
        "OrchestrationStatus": ".orchestrator",
        "RecipeOrchestrator": ".orchestrator",
        "StepResult": ".orchestrator",
        "Recipe": ".parser",
        "RecipeParser": ".parser",
        "RecipeStep": ".parser",
        "PipelineManager": ".pipeline_manager",
        "PipelineResult": ".pipeline_manager",
        "PipelineStage": ".pipeline_manager",
        "PipelineStatus": ".pipeline_manager",
        "PlanningContext": ".planner",
        "RecipePlanner": ".planner",
        "TaskComplexity": ".planner",
        "VerificationCriteria": ".planner",
        "ProgressCallback": ".progress_tracker",
        "ProgressPhase": ".progress_tracker",
        "ProgressSnapshot": ".progress_tracker",
        "ProgressTracker": ".progress_tracker",
        "PriorityTaskQueue": ".task_queue",
        "QueueTaskPriority": ".task_queue",
        "PluginLoader": ".plugin_loader",
        "PluginManifest": ".plugin_registry",
        "PluginRegistry": ".plugin_registry",
        "PluginStatus": ".plugin_registry",
        "PluginType": ".plugin_registry",
        "AgentProtocol": ".protocols",
        "StreamingMixin": ".protocols",
        "GeminiProvider": ".providers",
        "LLMProvider": ".providers",
        "LLMResponse": ".providers",
        "OfflineProvider": ".providers",
        "OpenAICompatibleProvider": ".providers",
        "RecipeRegistry": ".registry",
        "RegistryIndex": ".registry",
        "TelegramClient": ".telegram_client",
        "TelegramConfig": ".telegram_client",
        "send_alert": ".telegram_client",
        "PEVStructuredLogger": ".pev_structured_logger",
        "get_pev_logger": ".pev_structured_logger",
        "PEVMetricsCollector": ".pev_metrics_collector",
        "get_pev_metrics": ".pev_metrics_collector",
        "PEVDashboardData": ".pev_dashboard_data",
        "get_dashboard_data": ".pev_dashboard_data",
        "register_pev_health_checks": ".pev_health_checks",
        "get_pev_health_summary": ".pev_health_checks",
        "ExecutionResult": ".verifier",
        "RecipeVerifier": ".verifier",
        "VerificationCheck": ".verifier",
        "VerificationReport": ".verifier",
        "VerificationStatus": ".verifier",
        "MekongMcpServer": ".mcp_server",
        "mcp_server": ".mcp_server",
        "ConnectionCooldown": ".connection_cooldown",
        "CooldownState": ".connection_cooldown",
        "get_connection_cooldown": ".connection_cooldown",
        "reset_cooldown_singleton": ".connection_cooldown",
        "compress": ".compression",
        "sanitize": ".error_sanitizer",
        "MemoryBridge": ".memory_bridge",
        "MemoryKind": ".memory_bridge",
        "MemoryRecord": ".memory_bridge",
        "get_bridge": ".memory_bridge",
        "MemoryStoreAdapter": ".memory_store_adapter",
        "TelemetrySinkAdapter": ".telemetry_sink_adapter",
        "LLMRouterAdapter": ".llm_router_adapter",
    }

    if name in _imports:
        import importlib
        module = importlib.import_module(_imports[name], __package__)
        return getattr(module, name)

    # Fallback: expose submodules by name (enables patch("src.core.<mod>.<attr>"))
    try:
        import importlib
        submod = importlib.import_module(f".{name}", __package__)
        globals()[name] = submod  # cache for subsequent access
        return submod
    except (ImportError, ModuleNotFoundError):
        pass

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AgentBase", "Result", "Task", "TaskStatus",
    "AgentProtocol", "AgentRegistry", "StreamingMixin",
    "Alert", "AlertConfig", "AlertRouter", "AlertSeverity",
    "DAGScheduler", "DAGStepResult", "validate_dag",
    "RecipeExecutor", "ExecutionResult",
    "OrchestrationResult", "OrchestrationStatus", "RecipeOrchestrator", "StepResult",
    "Recipe", "RecipeParser", "RecipeStep",
    "PipelineManager", "PipelineResult", "PipelineStage", "PipelineStatus",
    "PlanningContext", "RecipePlanner", "TaskComplexity", "VerificationCriteria",
    "ProgressCallback", "ProgressPhase", "ProgressSnapshot", "ProgressTracker",
    "PriorityTaskQueue", "QueueTaskPriority",
    "PluginLoader", "PluginManifest", "PluginRegistry", "PluginStatus", "PluginType",
    "GeminiProvider", "LLMProvider", "LLMResponse", "OfflineProvider", "OpenAICompatibleProvider",
    "RecipeRegistry", "RegistryIndex",
    "TelegramClient", "TelegramConfig", "send_alert", "get_alert_router",
    "PEVStructuredLogger", "get_pev_logger",
    "PEVMetricsCollector", "get_pev_metrics",
    "PEVDashboardData", "get_dashboard_data",
    "register_pev_health_checks", "get_pev_health_summary",
    "RecipeVerifier", "VerificationCheck", "VerificationReport", "VerificationStatus",
    "MekongMcpServer", "mcp_server",
    "ConnectionCooldown", "CooldownState",
    "get_connection_cooldown", "reset_cooldown_singleton",
    "compress", "sanitize",
    "MemoryStoreAdapter", "TelemetrySinkAdapter", "LLMRouterAdapter",
]
