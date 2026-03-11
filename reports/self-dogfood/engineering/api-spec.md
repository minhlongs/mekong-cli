# OpenAPI Spec — /raas/* Endpoints
Generated: 2026-03-11

```yaml
openapi: "3.1.0"
info:
  title: Mekong CLI RaaS API
  version: "1.0.0"
  description: >
    Recipe-as-a-Service API. Submit goals for autonomous execution,
    poll/stream results, run named agents directly.
  license:
    name: MIT

servers:
  - url: https://agencyos-gateway.fly.dev
    description: Production (Fly.io, Singapore)
  - url: http://localhost:8000
    description: Local dev

security:
  - bearerAuth: []

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT   # also accepts mk_<base64> API keys

  schemas:
    TaskStatus:
      type: string
      enum: [pending, running, success, failed, partial, rolled_back]

    TaskRequest:
      type: object
      required: [goal]
      properties:
        goal:
          type: string
          minLength: 1
          description: High-level goal to execute
          example: "Create a FastAPI endpoint with JWT auth"
        agent:
          type: string
          nullable: true
          description: Preferred agent name (e.g. 'git', 'shell')
        recipe:
          type: string
          nullable: true
          description: Path to recipe YAML file to run directly
        options:
          type: object
          additionalProperties: true
          description: Extra orchestrator options

    TaskResponse:
      type: object
      properties:
        task_id:
          type: string
          format: uuid
        status:
          $ref: '#/components/schemas/TaskStatus'
        tenant_id:
          type: string

    StepDetail:
      type: object
      properties:
        order:
          type: integer
        title:
          type: string
        passed:
          type: boolean
        exit_code:
          type: integer
        summary:
          type: string

    TaskStatusResponse:
      type: object
      properties:
        task_id:
          type: string
          format: uuid
        status:
          $ref: '#/components/schemas/TaskStatus'
        goal:
          type: string
        tenant_id:
          type: string
        total_steps:
          type: integer
        completed_steps:
          type: integer
        failed_steps:
          type: integer
        success_rate:
          type: number
          format: float
          minimum: 0.0
          maximum: 1.0
        errors:
          type: array
          items:
            type: string
        warnings:
          type: array
          items:
            type: string
        steps:
          type: array
          items:
            $ref: '#/components/schemas/StepDetail'

    AgentInfo:
      type: object
      properties:
        name:
          type: string
        description:
          type: string

    AgentRunRequest:
      type: object
      required: [goal]
      properties:
        goal:
          type: string
        options:
          type: object

    AgentRunResponse:
      type: object
      properties:
        agent:
          type: string
        status:
          type: string
          enum: [success, failed]
        output:
          type: string

    Error:
      type: object
      properties:
        detail:
          type: string

paths:
  /v1/tasks:
    post:
      summary: Submit a goal for execution
      operationId: submitTask
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TaskRequest'
      responses:
        "202":
          description: Task accepted
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskResponse'
        "401":
          description: Missing or invalid Bearer token
        "402":
          description: Insufficient credits
        "422":
          description: Validation error

  /v1/tasks/{task_id}:
    get:
      summary: Poll task status and results
      operationId: getTaskStatus
      parameters:
        - name: task_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        "200":
          description: Task status
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskStatusResponse'
        "404":
          description: Task not found or belongs to different tenant

  /v1/tasks/{task_id}/stream:
    get:
      summary: Stream task progress as SSE
      operationId: streamTask
      parameters:
        - name: task_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        "200":
          description: Server-Sent Event stream
          content:
            text/event-stream:
              schema:
                type: string
              example: |
                data: {"type":"step","order":1,"title":"Scaffold","passed":true,"exit_code":0,"completed":1,"total":4}

                data: {"type":"complete","status":"success","success_rate":1.0,"errors":[]}
        "404":
          description: Task not found

  /v1/agents:
    get:
      summary: List registered agents
      operationId: listAgents
      responses:
        "200":
          description: Agent list
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/AgentInfo'

  /v1/agents/{name}/run:
    post:
      summary: Run a named agent directly
      operationId: runAgent
      parameters:
        - name: name
          in: path
          required: true
          schema:
            type: string
          example: git
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AgentRunRequest'
      responses:
        "200":
          description: Agent output
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AgentRunResponse'
        "404":
          description: Agent not found (includes available list)
        "500":
          description: Agent execution error
```
