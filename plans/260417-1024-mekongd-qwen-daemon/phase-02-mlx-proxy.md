# Phase 02 — MLX Loader + Anthropic-compat `/v1/messages` + SSE Streaming

## Context Links

- Plan: [plan.md](./plan.md)
- Phase 01 (deps): [phase-01-scaffold.md](./phase-01-scaffold.md)
- Research: [research-260417-1024-qwen36-solo-company.md](../reports/research-260417-1024-qwen36-solo-company.md)
- Anthropic Messages API spec: https://docs.anthropic.com/en/api/messages

## Overview

- **Priority:** P1
- **Status:** pending (blocked by Phase 01)
- **Description:** Wire MLX Qwen3.6 loader into a FastAPI server with Anthropic-compatible `/v1/messages` POST endpoint. Support both non-streaming (JSON response) and streaming (SSE) per Anthropic schema. No routing logic, no stats writes — pure forward to local MLX. Phase 03 later wraps this with router + stats.

## Key Insights

- CC CLI subagent calls hit Anthropic Messages API with `stream: true` by default — SSE is mandatory for compatibility.
- `mlx-lm` exposes `load()` + `stream_generate()` — streaming is native, no extra threading.
- Anthropic SSE events: `message_start`, `content_block_start`, `content_block_delta` (type=`text_delta`), `content_block_stop`, `message_delta`, `message_stop`. Must emit all six to satisfy CC CLI parser.
- Import MLX lazily inside `runtime.py` — keeps Phase 01 install path clean on non-Apple Silicon (CI Linux).
- CI cannot download 19GB Q4 weights — use `pytest.mark.requires_model` skip + mock runtime for test.

## Requirements

### Functional

- `POST /v1/messages` accepts Anthropic request body (`model`, `messages`, `system`, `max_tokens`, `stream`, etc.).
- If `stream=false`: returns JSON `Message` object with `content: [{type:"text", text:"..."}]` + `usage` counts.
- If `stream=true`: returns `text/event-stream` emitting full 6-event Anthropic sequence.
- `GET /health` returns `{"status":"ok","model":"<loaded-model-id>"}`.
- `mekongd serve` (from Phase 01 stub) now boots uvicorn on `Settings.host:port`.
- Model loader is lazy — first request triggers load; subsequent requests reuse cached instance.

### Non-Functional

- Startup log: `"mekongd serve on 127.0.0.1:8765 | model=<path> | ready"`.
- Time-to-first-token < 500ms for warm model (tested w/ mock).
- Graceful shutdown on SIGTERM (uvicorn default).
- MLX import behind `try/except ImportError` — clear error message on non-Mac.

## Architecture

```
                HTTP POST /v1/messages
                        |
                        v
         +------------------------------+
         |  proxy.py (FastAPI app)      |
         |  - validate schemas.py types |
         |  - if stream: SSE generator  |
         |  - else: JSON response       |
         +---------------+--------------+
                         |
                         v
         +------------------------------+
         |  runtime.py                  |
         |  QwenRuntime (singleton)     |
         |  - load() [mlx_lm.load]      |
         |  - stream_tokens(prompt)     |
         |  - format prompt (ChatML)    |
         +---------------+--------------+
                         |
                         v
               mlx_lm model in RAM
               (Q4 ~20GB on M1 Max)
```

SSE event sequence:
```
event: message_start      data: {type,message:{id,role:assistant,...}}
event: content_block_start data: {type,index:0,content_block:{type:text,text:""}}
event: content_block_delta data: {type,index:0,delta:{type:text_delta,text:"Hi"}}
  ... (N deltas) ...
event: content_block_stop  data: {type,index:0}
event: message_delta       data: {type,delta:{stop_reason,stop_sequence},usage}
event: message_stop        data: {type}
```

## Related Code Files

### To Create

- `/Users/macbookprom1/mekong-cli/packages/mekongd/mekongd/schemas.py`
- `/Users/macbookprom1/mekong-cli/packages/mekongd/mekongd/runtime.py`
- `/Users/macbookprom1/mekong-cli/packages/mekongd/mekongd/proxy.py`
- `/Users/macbookprom1/mekong-cli/packages/mekongd/tests/test_proxy.py` (integration, uses mock runtime)
- `/Users/macbookprom1/mekong-cli/packages/mekongd/tests/conftest.py` (mock fixture)

### To Modify

- `/Users/macbookprom1/mekong-cli/packages/mekongd/mekongd/cli.py` — replace `serve` stub with real uvicorn boot
- `/Users/macbookprom1/mekong-cli/packages/mekongd/pyproject.toml` — move `fastapi/uvicorn/sse-starlette/httpx` from extras to core deps

## Implementation Steps

1. Define pydantic models in `schemas.py`:
   ```python
   class ContentBlock(BaseModel):
       type: Literal["text"]; text: str
   class Message(BaseModel):
       role: Literal["user","assistant"]; content: str | list[ContentBlock]
   class MessagesRequest(BaseModel):
       model: str; messages: list[Message]; system: str | None = None
       max_tokens: int = 1024; stream: bool = False; temperature: float = 1.0
   class Usage(BaseModel):
       input_tokens: int; output_tokens: int
   class MessagesResponse(BaseModel):
       id: str; type: Literal["message"] = "message"; role: Literal["assistant"] = "assistant"
       content: list[ContentBlock]; model: str; stop_reason: str | None = None
       usage: Usage
   ```
2. Implement `runtime.py`:
   ```python
   class QwenRuntime:
       def __init__(self, model_path: Path): self.model_path = model_path; self._mdl = None; self._tok = None
       def load(self) -> None:  # lazy mlx_lm.load
           from mlx_lm import load
           self._mdl, self._tok = load(str(self.model_path))
       def format_prompt(self, system: str|None, messages: list[Message]) -> str: ...  # ChatML
       def stream_tokens(self, prompt: str, max_tokens: int, temperature: float) -> Iterator[str]:
           from mlx_lm import stream_generate
           yield from stream_generate(self._mdl, self._tok, prompt, max_tokens=max_tokens)
   _runtime: QwenRuntime | None = None
   def get_runtime(settings: Settings) -> QwenRuntime: ...  # singleton
   ```
3. Implement `proxy.py` FastAPI app:
   ```python
   app = FastAPI(title="mekongd")
   @app.get("/health") async def health(): ...
   @app.post("/v1/messages") async def messages(req: MessagesRequest, settings: Settings = Depends(load_settings)):
       rt = get_runtime(settings)
       if not req.stream:
           text = "".join(rt.stream_tokens(rt.format_prompt(req.system, req.messages), req.max_tokens, req.temperature))
           return MessagesResponse(id=f"msg_{uuid4().hex[:12]}", content=[ContentBlock(type="text", text=text)], model=req.model, stop_reason="end_turn", usage=Usage(...))
       return EventSourceResponse(_sse_generator(rt, req))
   async def _sse_generator(rt, req) -> AsyncIterator[dict]:  # emit 6-event sequence
       ...
   ```
4. Update `cli.py` `serve` command: `uvicorn.run("mekongd.proxy:app", host=..., port=..., log_level="info")`.
5. Move `fastapi`, `uvicorn[standard]`, `sse-starlette`, `httpx` from `[proxy]` extra into core deps in `pyproject.toml`.
6. Create `conftest.py` with `mock_runtime` fixture: replaces `get_runtime` to return deterministic token stream `["Hello", " ", "world"]`.
7. Write `tests/test_proxy.py`:
   - non-stream: `TestClient(app).post("/v1/messages", json={...stream:False})` → assert `content[0].text == "Hello world"`.
   - stream: collect SSE events, assert 6 event types present in order, assert `text_delta` concat == `"Hello world"`.
   - `/health` returns 200 with `status=ok`.
8. Add `pytest.mark.requires_model` marker in `pyproject.toml` `[tool.pytest.ini_options]`; mark any test using real MLX weights.
9. Verify: `mekongd serve --port 8765` → curl non-stream + stream against mock → 200 + correct shape.

## Todo List

- [ ] Write `schemas.py` (Anthropic-compat pydantic types)
- [ ] Write `runtime.py` (QwenRuntime, lazy MLX import, singleton)
- [ ] Write `proxy.py` (FastAPI app, `/v1/messages`, `/health`, SSE generator)
- [ ] Update `cli.py` `serve` to boot uvicorn
- [ ] Promote `fastapi/uvicorn/sse-starlette/httpx` to core deps
- [ ] Add `requires_model` pytest marker
- [ ] Write `conftest.py` with mock runtime fixture
- [ ] Write `tests/test_proxy.py` (non-stream + stream + health)
- [ ] Local curl smoke-test `/v1/messages` (mock runtime)

## Success Criteria

- `mekongd serve` boots uvicorn without errors (mock runtime) on any OS.
- `curl -X POST localhost:8765/v1/messages -d '{"model":"qwen3.6","messages":[...],"stream":false}'` → 200 JSON Anthropic shape.
- Streaming curl returns 6 SSE event types in correct order.
- `pytest packages/mekongd/tests/test_proxy.py` green on Linux CI (mock) and M1 Max (real, if marker enabled).
- No MLX import errors on Linux CI.

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| MLX install fails on Linux CI | Lazy import inside `runtime.load()`; tests always use mock fixture |
| Anthropic SSE schema drift | Pin `anthropic>=0.40.0` (matches main repo); snapshot-test event shapes |
| First-load latency > 30s on 35B model | Warm-load option: `mekongd serve --preload`; not required for v0 |
| `sse-starlette` event formatting quirks | Use `EventSourceResponse` + dict payload; verify via test |
| Tokenizer ChatML format wrong for Qwen3.6 | Follow `mlx-lm` example for Qwen3 (apply_chat_template from tokenizer) |

## Security Considerations

- Bind default to `127.0.0.1` only (Settings default) — NEVER `0.0.0.0` in v0.
- No auth on `/v1/messages` in v0 — MUST document in README as "localhost-only, do not expose".
- Request body size limit: FastAPI default (1MB) sufficient; no uploads.
- Log redaction: never log full prompt content at INFO level (use DEBUG).

## Next Steps

- Phase 03 wraps `/v1/messages` handler with router decision (local vs cloud) and stats recording.
- Phase 03 will introduce `httpx.AsyncClient` for cloud fallback to Anthropic.

## Unresolved Questions

1. Tool-use support (`tools:` in request body) — pass-through only or full support? (defer: v0 = text-only; tools path hits cloud always via Phase 03 router rule)
2. Handle `anthropic-version` header — echo back or ignore? (ignore in v0)
3. Token counting: use `mlx_lm` tokenizer length vs Anthropic's count endpoint? (use MLX tokenizer length; document as approximate)
