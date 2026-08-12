# Autonomous Goal Engine

> The PEV (Plan→Execute→Verify) engine for autonomous goal execution with checkpoints and verification

**Last Updated**: 2026-06-20
**Implementation**: `src/core/pev/`
**CLI Commands**: `mekong cook-auto`, `mekong plan-auto`
**Related**: [Command Fabric](command-fabric.md), [Constitutional AI](constitutional-ai.md), [Economic Particles](economic-particles.md)

---

## Overview

The Autonomous Goal Engine (AGE) is the core orchestration system that enables **autonomous goal execution** in Mekong CLI. It transforms high-level goals into executable plans, runs them with automatic checkpointing, and verifies outcomes before marking completion.

### Key Characteristics

- **Goal Decomposition**: Breaks complex goals into atomic tasks with dependencies
- **Checkpoint Persistence**: State persisted to database for crash recovery
- **Automatic Retry**: Exponential backoff on transient failures
- **Verification Gates**: Output validation before progression
- **Constitutional Compliance**: AI actions reviewed against 9 principles
- **MCU-Aware**: Tracks credit consumption per goal

### The PEV Loop

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS GOAL ENGINE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                      PLAN PHASE                               │  │
│  │  • Goal analysis (LLM decomposition)                         │  │
│  │  • Task extraction with dependencies                         │  │
│  │  • Resource estimation (MCU, time)                           │  │
│  │  • Verification criteria definition                          │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     EXECUTE PHASE                             │  │
│  │  • Task scheduling (respects dependencies)                   │  │
│  │  • Command execution (via Command Fabric)                    │  │
│  │  • Checkpoint persistence after each task                   │  │
│  │  • Error handling with retry/backoff                        │  │
│  │  • Constitutional review for AI actions                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     VERIFY PHASE                              │  │
│  │  • Output validation (user-provided verifier)                │  │
│  │  • Rollback on verification failure                         │  │
│  │  • Success criteria evaluation                              │  │
│  │  • Goal state update (complete/failed)                      │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Architecture Components

### 1. Goal Model

Goals are persisted as structured records:

```python
@dataclass
class Goal:
    id: str                          # UUIDv7
    title: str                       # Human-readable title
    description: str                 # Full goal description
    status: GoalStatus               # pending|running|paused|completed|failed
    created_by: str                  # User ID
    created_at: datetime             # Creation timestamp
    updated_at: datetime             # Last update

    # PEV State
    plan: List[Task]                 # Decomposed tasks
    current_task_id: Optional[str]  # Currently executing task
    checkpoint_data: dict           # Serialized execution state

    # Metrics
    total_mcu_estimated: float      # Estimated cost
    total_mcu_actual: float         # Actual cost
    tasks_completed: int
    tasks_failed: int

    # Metadata
    profile: str                     # Execution profile (smoke/standard/deep)
    tags: List[str]                 # For organization
```

### 2. Task Model

Each goal decomposes into atomic tasks:

```python
@dataclass
class Task:
    id: str                         # Task UUID
    goal_id: str                    # Parent goal
    title: str                      # Task description
    command: str                    # Mekong command to execute
    arguments: dict                 # Command arguments
    status: TaskStatus              # pending|running|completed|failed|skipped

    # Dependencies
    depends_on: List[str]           # Task IDs that must complete first
    parallelizable: bool            # Can run with other tasks

    # Verification
    verify_command: Optional[str]   # Command to verify task completion
    verify_arguments: Optional[dict]

    # State
    result: Optional[str]           # Command output
    error: Optional[str]            # Error message if failed
    retry_count: int                # Number of retry attempts
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
```

### 3. PEV Orchestrator

The main orchestrator coordinating the PEV loop:

```python
class PEVOrchestrator:
    """Main autonomous goal execution engine."""

    def __init__(
        self,
        planner: Planner,
        executor: Executor,
        verifier: Verifier,
        repository: GoalRepository,
        constitution: Optional[Constitution] = None
    ):
        self.planner = planner
        self.executor = executor
        self.verifier = verifier
        self.repository = repository
        self.constitution = constitution

    async def execute_goal(
        self,
        goal_id: str,
        auto_confirm: bool = False
    ) -> GoalResult:
        """Execute a goal through PEV loop."""
        # 1. Load goal
        goal = await self.repository.get(goal_id)

        # 2. Plan (if not already planned)
        if not goal.plan:
            goal = await self.planner.plan_goal(goal)

        # 3. Execute tasks
        while not self._all_tasks_done(goal):
            task = self._select_next_task(goal)
            if not task:
                break  # No runnable tasks (waiting on dependencies)

            # Constitutional review for AI tasks
            if self._requires_constitutional_review(task):
                review = await self.constitution.review(
                    action=f"goal:task:{task.id}",
                    context={"goal_id": goal_id, "task_id": task.id},
                    parameters=task.arguments
                )
                if not review.passed:
                    task.status = TaskStatus.FAILED
                    task.error = f"Constitutional violation: {review.failed_principles}"
                    break

            # Execute
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            await self.repository.save_task(task)

            try:
                result = await self.executor.execute_task(task)
                task.result = result.output
                task.duration_ms = result.duration_ms

                # Verify
                if task.verify_command:
                    verified = await self.verifier.verify_task(task)
                    if not verified:
                        task.status = TaskStatus.FAILED
                        task.error = "Verification failed"
                        if auto_confirm:
                            await self._rollback_task(task)
                        break

                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)

            await self.repository.save_task(task)

        # 4. Finalize goal
        goal_status = self._compute_goal_status(goal)
        goal.status = goal_status
        goal.updated_at = datetime.utcnow()
        await self.repository.save_goal(goal)

        return GoalResult.from_goal(goal)
```

### 4. Planner

Decomposes goals into executable tasks using LLM:

```python
class Planner:
    """Decomposes goals into task plans."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def plan_goal(self, goal: Goal) -> Goal:
        """Generate task plan for a goal."""

        prompt = f"""
        Decompose this goal into executable tasks:

        GOAL: {goal.description}

        Output JSON:
        {{
          "tasks": [
            {{
              "id": "uuid",
              "title": "Task description",
              "command": "mekong <command>",
              "arguments": {{}},
              "depends_on": ["task_uuid"],
              "parallelizable": false,
              "verify_command": "mekong verify ..."
            }}
          ]
        }}

        Rules:
        - Each task must be a single mekong command
        - Dependencies must be explicit (can't run B before A)
        - Include verification commands where applicable
        - Max 20 tasks per goal (split larger goals)
        """

        response = await self.llm.generate(prompt)
        plan_data = json.loads(response)

        for task_data in plan_data["tasks"]:
            task = Task(
                id=task_data["id"],
                goal_id=goal.id,
                title=task_data["title"],
                command=task_data["command"],
                arguments=task_data.get("arguments", {}),
                depends_on=task_data.get("depends_on", []),
                parallelizable=task_data.get("parallelizable", False),
                verify_command=task_data.get("verify_command"),
                verify_arguments=task_data.get("verify_arguments", {})
            )
            goal.plan.append(task)

        return goal
```

### 5. Executor

Executes tasks with retry logic and checkpointing:

```python
class Executor:
    """Executes tasks with retry and checkpointing."""

    def __init__(
        self,
        command_registry: CommandRegistry,
        max_retries: int = 3,
        base_delay_ms: int = 1000
    ):
        self.registry = command_registry
        self.max_retries = max_retries
        self.base_delay_ms = base_delay_ms

    async def execute_task(self, task: Task) -> ExecutionResult:
        """Execute a single task with retry."""

        for attempt in range(self.max_retries + 1):
            try:
                # Resolve command from fabric
                command_spec = self.registry.get_command(task.command)
                if not command_spec:
                    raise ValueError(f"Command not found: {task.command}")

                # Check MCU balance
                mcu_cost = command_spec.mcu_cost
                if not await self._deduct_mcu(task, mcu_cost):
                    raise InsufficientBalanceError(f"Need {mcu_cost} MCU")

                # Execute
                start = time.time()
                result = await command_spec.handler(**task.arguments)
                duration_ms = (time.time() - start) * 1000

                # Record particle (billing event)
                await self._record_usage_particle(task, mcu_cost, duration_ms)

                return ExecutionResult(
                    output=result,
                    duration_ms=duration_ms,
                    mcu_used=mcu_cost
                )

            except (TransientError, TimeoutError) as e:
                if attempt < self.max_retries:
                    delay = self.base_delay_ms * (2 ** attempt)  # Exponential backoff
                    await asyncio.sleep(delay / 1000)
                    continue
                raise

        raise MaxRetriesExceededError(f"Failed after {self.max_retries} attempts")
```

### 6. Verifier

Validates task completion:

```python
class Verifier:
    """Verifies task completion."""

    async def verify_task(self, task: Task) -> bool:
        """Run verification command and check result."""

        if not task.verify_command:
            return True  # No verification required

        command_spec = self.registry.get_command(task.verify_command)
        if not command_spec:
            return False

        try:
            result = await command_spec.handler(
                **(task.verify_arguments or {})
            )

            # Verification succeeded if command returns truthy
            return bool(result)

        except Exception as e:
            logger.error(f"Verification failed for task {task.id}: {e}")
            return False
```

---

## CLI Interface

### cook-auto

The primary command for autonomous goal execution:

```bash
# Basic usage
mekong cook-auto "Build a SaaS landing page with Stripe integration"

# With profile (affects planning depth and MCU budget)
mekong cook-auto "Launch marketing campaign" --profile smoke    # Fast, cheap
mekong cook-auto "Launch marketing campaign" --profile standard  # Balanced
mekong cook-auto "Research competitor analysis" --profile deep   # Thorough

# Resume interrupted goal
mekong cook-auto --resume goal_abc123

# Auto mode (no interactive prompts)
mekong cook-auto "Deploy to production" --auto
```

**Contract** (`cook-auto.json`):
```json
{
  "command": "cook-auto",
  "description": "Autonomous goal execution with PEV engine",
  "arguments": [
    {"name": "goal", "type": "string", "required": true},
    {"name": "--profile", "type": "enum", "options": ["smoke", "standard", "deep"]},
    {"name": "--resume", "type": "string"},
    {"name": "--auto", "type": "flag"}
  ],
  "output": {
    "goal_id": "string",
    "status": "completed|failed",
    "tasks_total": 0,
    "tasks_completed": 0,
    "mcu_used": 0.0,
    "duration_ms": 0
  }
}
```

### plan-auto

Generate a plan without execution:

```bash
mekong plan-auto "Q2 marketing strategy" --output plan.json

# Preview plan
mekong plan-auto "Hire 3 engineers" --dry-run
```

### Goal Status Commands

```bash
# List all goals
mekong goal list

# View goal details
mekong goal show goal_abc123

# Pause running goal
mekong goal pause goal_abc123

# Resume paused goal
mekong goal resume goal_abc123

# Cancel goal (with rollback)
mekong goal cancel goal_abc123

# Retry failed task
mekong goal retry goal_abc123 --task task_def456
```

---

## JSON Contracts

### Goal Contract (`goal.json`)

```json
{
  "id": "goal_abc123",
  "title": "Deploy to Cloudflare",
  "description": "Complete deployment pipeline setup",
  "status": "running",
  "created_by": "user_123",
  "created_at": "2025-06-20T10:00:00Z",
  "updated_at": "2025-06-20T10:05:00Z",
  "profile": "standard",
  "plan": [
    {
      "id": "task_1",
      "title": "Create wrangler.toml",
      "command": "mekong write",
      "arguments": {"file": "wrangler.toml", "content": "..."},
      "depends_on": [],
      "status": "completed",
      "started_at": "2025-06-20T10:01:00Z",
      "completed_at": "2025-06-20T10:01:05Z",
      "duration_ms": 5000,
      "mcu_used": 0.5
    },
    {
      "id": "task_2",
      "title": "Run deployment",
      "command": "mekong deploy",
      "arguments": {"provider": "cloudflare"},
      "depends_on": ["task_1"],
      "status": "running"
    }
  ],
  "checkpoint_data": {
    "current_task_index": 1,
    "saved_state": {}
  },
  "metrics": {
    "total_mcu_estimated": 5.0,
    "total_mcu_actual": 1.5,
    "tasks_completed": 1,
    "tasks_failed": 0
  }
}
```

### Status Command Contract

```json
{
  "command": "goal-status",
  "description": "Get goal execution status",
  "arguments": [
    {"name": "goal_id", "type": "string", "required": true}
  ],
  "output": {
    "goal_id": "string",
    "status": "pending|running|paused|completed|failed",
    "progress": {
      "completed": 0,
      "total": 0,
      "percent": 0.0
    },
    "current_task": {
      "id": "string",
      "title": "string",
      "started_at": "timestamp"
    },
    "next_tasks": ["task_id"],
    "blocked_tasks": ["task_id"],
    "duration_ms": 0,
    "mcu_used": 0.0
  }
}
```

---

## Database Schema

### goals Table

```sql
CREATE TABLE goals (
    id VARCHAR(36) PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- PEV state
    plan JSONB NOT NULL DEFAULT '[]',
    current_task_id VARCHAR(36),
    checkpoint_data JSONB DEFAULT '{}',

    -- Metadata
    profile VARCHAR(20) DEFAULT 'standard',
    tags JSONB DEFAULT '[]',

    -- Metrics
    total_mcu_estimated DECIMAL(10, 3) DEFAULT 0,
    total_mcu_actual DECIMAL(10, 3) DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    tasks_failed INTEGER DEFAULT 0
);

CREATE INDEX idx_goals_status ON goals(status);
CREATE INDEX idx_goals_created_by ON goals(created_by);
CREATE INDEX idx_goals_created_at ON goals(created_at);
```

### goal_tasks Table

```sql
CREATE TABLE goal_tasks (
    id VARCHAR(36) PRIMARY KEY,
    goal_id VARCHAR(36) NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    command TEXT NOT NULL,
    arguments JSONB DEFAULT '{}',

    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    depends_on JSONB DEFAULT '[]',
    parallelizable BOOLEAN DEFAULT false,

    verify_command TEXT,
    verify_arguments JSONB DEFAULT '{}',

    result TEXT,
    error TEXT,
    retry_count INTEGER DEFAULT 0,

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_goal_tasks_goal_id ON goal_tasks(goal_id);
CREATE INDEX idx_goal_tasks_status ON goal_tasks(status);
CREATE INDEX idx_goal_tasks_depends_on ON goal_tasks USING GIN(depends_on);
```

### goal_checkpoints Table (for persistence)

```sql
CREATE TABLE goal_checkpoints (
    id SERIAL PRIMARY KEY,
    goal_id VARCHAR(36) NOT NULL REFERENCES goals(id),
    checkpoint_number INTEGER NOT NULL,
    state JSONB NOT NULL,
    task_id VARCHAR(36),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_goal_checkpoints_goal_id ON goal_checkpoints(goal_id);
CREATE UNIQUE INDEX idx_goal_checkpoints_unique ON goal_checkpoints(goal_id, checkpoint_number);
```

---

## Integration Points

### Constitutional AI

All AI-powered planning is subject to constitutional review:

```python
# In planner
review = await constitution.review(
    action="goal:plan",
    context={"goal_id": goal.id, "user_id": goal.created_by},
    parameters={"goal_description": goal.description},
    metadata={"profile": goal.profile}
)

if review.overall_score < 0.5:
    raise ConstitutionalViolationError(
        "Goal planning blocked",
        failed_principles=review.failed_principles
    )
```

### Command Fabric

Tasks execute commands from the fabric catalog:

```python
spec = command_registry.get_command(task.command)
if not spec:
    raise CommandNotFoundError(task.command)

# Execute with fabric runtime
result = await fabric_runtime.invoke(
    command=spec.name,
    arguments=task.arguments,
    plugin=spec.plugin
)
```

### MCU Billing

Each task deducts MCU credits:

```python
# In executor
cost = command_spec.mcu_cost
if not await mcu_manager.check_and_deduct(
    user_id=goal.created_by,
    command=task.command,
    mcu_cost=cost
):
    raise InsufficientBalanceError(f"Need {cost} MCU")
```

### Economic Particles

Goal execution creates usage particles:

```python
# After task completes
particle = EconomicParticle(
    key_id=user.key_id,
    particle_type=PARTICLE_TYPE_USAGE,
    amount=Decimal(str(-task_mcu_cost)),
    currency=CURRENCY_USD,
    balance_after=await repo.get_balance(user.key_id),
    metadata={
        "goal_id": goal.id,
        "task_id": task.id,
        "command": task.command,
        "duration_ms": task.duration_ms
    },
    source=SOURCE_API
)
await particle_repo.create_particle(particle)
```

---

## Profiles

### smoke (Fast, Cheap)

- **Planning**: Single LLM call, minimal task breakdown
- **MCU Budget**: ~5 MCU per goal
- **Verification**: Optional, user-triggered only
- **Use Case**: Quick prototyping, testing

### standard (Balanced)

- **Planning**: Full decomposition with dependency analysis
- **MCU Budget**: ~20 MCU per goal
- **Verification**: Automatic for critical tasks
- **Use Case**: Typical business operations

### deep (Thorough)

- **Planning**: Multiple LLM calls with validation
- **MCU Budget**: ~50 MCU per goal
- **Verification**: All tasks verified automatically
- **Retries**: Up to 5 attempts per task
- **Use Case**: Critical deployments, migrations

---

## Error Handling & Recovery

### Transient Errors (Auto-Retry)

```python
TRANSIENT_ERRORS = {
    TimeoutError,
    ConnectionError,
    RateLimitError,
    ServiceUnavailableError
}

# Exponential backoff
retry_delay = base_delay * (2 ** attempt) + jitter
```

### Non-Recoverable Errors

These trigger immediate failure:

- Constitutional violations
- Insufficient balance
- Command not found
- Invalid arguments (validation error)
- Resource limits exceeded

### Rollback

On verification failure with `--auto`:

```python
async def rollback_goal(goal: Goal) -> None:
    """Rollback completed tasks in reverse order."""

    completed_tasks = [t for t in goal.plan if t.status == TaskStatus.COMPLETED]
    for task in reversed(completed_tasks):
        if task.rollback_command:
            await self.executor.execute_rollback(task)
        task.status = TaskStatus.ROLLED_BACK

    goal.status = GoalStatus.ROLLED_BACK
```

---

## Monitoring & Observability

### Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `goal_executions_total` | counter | Goals started by profile |
| `goal_duration_seconds` | histogram | Time to completion by status |
| `task_executions_total` | counter | Tasks executed by command |
| `task_retry_total` | counter | Retry attempts |
| `checkpoint_created_total` | counter | Checkpoints persisted |
| `verification_failures_total` | counter | Verification failures |

### Logs

Structured log events:
```json
{
  "event": "goal.execution.started",
  "goal_id": "goal_abc123",
  "user_id": "user_123",
  "profile": "standard",
  "estimated_tasks": 15,
  "estimated_mcu": 12.5
}

{
  "event": "task.executed",
  "goal_id": "goal_abc123",
  "task_id": "task_def456",
  "command": "mekong deploy",
  "status": "completed|failed",
  "duration_ms": 4250,
  "mcu_used": 1.5,
  "retry_count": 0
}

{
  "event": "goal.execution.completed",
  "goal_id": "goal_abc123",
  "status": "completed|failed",
  "duration_ms": 45000,
  "total_mcu": 18.5,
  "tasks_completed": 15,
  "tasks_failed": 0
}
```

---

## Best Practices

### 1. Idempotent Commands

Design commands to be safely re-runnable:

```python
# Good: Check before creating
if not await db.table_exists("users"):
    await db.create_table("users")

# Avoid: Blind creation
await db.execute("CREATE TABLE users ...")  # Fails on re-run
```

### 2. Verification Commands

Always include verification for critical tasks:

```json
{
  "command": "mekong deploy",
  "verify_command": "mekong health",
  "verify_arguments": {"service": "api"}
}
```

### 3. Atomic Checkpoints

Checkpoint after every significant state change:

```python
await goal_repository.save_checkpoint(
    goal_id=goal.id,
    task_id=task.id,
    state={"completed_tasks": [...], "current_task": task.id}
)
```

### 4. Resource Budgets

Set reasonable MCU budgets per profile:

```python
PROFILE_BUDGETS = {
    "smoke": 5.0,
    "standard": 20.0,
    "deep": 50.0
}
```

---

## Troubleshooting

### Goal Stuck in "running"

```bash
# Check current task
mekong goal show goal_abc123

# Force pause
mekong goal pause goal_abc123

# Investigate task logs
mekong log tail --goal goal_abc123

# If task is hung, cancel with rollback
mekong goal cancel goal_abc123 --rollback
```

### Frequent Task Failures

Check:
1. Command syntax (run manually to verify)
2. MCU balance (`mekong balance`)
3. Constitutional compliance (`mekong constitutional-review --task <id>`)
4. Dependencies (are prerequisite tasks completing?)

### High MCU Usage

- Review `PROFILE_BUDGETS` settings
- Check for runaway loops in task commands
- Enable `--dry-run` to preview cost before execution

---

## References

- **Implementation**: `src/core/pev/` (planner.py, executor.py, verifier.py, orchestrator.py)
- **Models**: `src/models/goal.py`, `src/models/task.py`
- **CLI Commands**: `src/cli/goal_commands.py`
- **Repository**: `src/core/goal_repository.py`
- **Tests**: `tests/pev/test_*.py`
- **Command Fabric**: [docs/command-fabric.md](./command-fabric.md)
- **Constitutional AI**: [docs/constitutional-ai.md](./constitutional-ai.md)

---

**Next**: Learn about [Economic Particles](economic-particles.md) to understand the financial layer, or explore [Command Fabric](command-fabric.md) for the unified command catalog.
