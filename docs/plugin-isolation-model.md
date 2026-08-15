# Plugin Isolation Model

**Version**: 1.0.0
**Date**: 2026-06-20
**Status**: Stable

This document describes the isolation mechanisms available for Mekong CLI plugins and how to configure them.

## Overview

Plugin isolation protects the core system and other plugins from misbehaving code. Mekong CLI supports three isolation levels, each providing different security-performance trade-offs.

## Isolation Levels

### Level 1: Process Isolation (Default)

**Technology**: Subprocess with resource limits
**Security**: Medium
**Performance**: Minimal overhead (~5%)
**Use Case**: Most plugins, trusted developers

**Characteristics**:
- Plugin runs in separate OS process
- Memory limit enforced via `resource.setrlimit()`
- CPU time limit via `resource.RLIMIT_CPU`
- File system access restricted to plugin directory
- IPC via stdio JSON-RPC

**Configuration**:
```json
{
  "loadingMode": "process",
  "resources": {
    "memory": 256,
    "cpuTime": 30000
  }
}
```

**Resource Limits**:
- Memory: 256MB (soft), 512MB (hard)
- CPU time: 30 seconds
- Open files: 256
```

### Level 2: Container Isolation

**Technology**: Docker container with seccomp/apparmor
**Security**: High
**Performance**: Moderate overhead (~15-20%)
**Use Case**: Third-party plugins, marketplace submissions

**Characteristics**:
- Full filesystem sandbox with read-only root
- Network isolation (outbound only by default)
- Seccomp profile blocking dangerous syscalls
- AppArmor/SELinux confinement
- Resource limits enforced by cgroups

**Configuration**:
```json
{
  "loadingMode": "process",
  "sandbox": {
    "enabled": true,
    "v8Isolate": false,
    "allowedHosts": ["https://api.mekong.dev"],
    "blockedModules": ["subprocess", "socket", "ctypes"]
  },
  "resources": {
    "memory": 512,
    "cpuTime": 60000
  }
}
```

**Security Features**:
- Read-only root filesystem (except `/tmp` and plugin data dir)
- Network namespace (outbound to allowed hosts only)
- PID namespace (plugin sees only its own process)
- No capability escalation

### Level 3: VM Isolation

**Technology**: Firecracker microVM
**Security**: Maximum
**Performance**: Higher overhead (~30-40%)
**Use Case**: Highly sensitive operations, compliance requirements

**Characteristics**:
- Full hardware virtualization
- Kernel isolation
- Network bridge with firewall
- vCPU and memory hard limits
- Encrypted root filesystem

**Configuration**:
```json
{
  "loadingMode": "wasm",
  "resources": {
    "memory": 1024,
    "cpuTime": 120000,
    "storage": 1000
  },
  "sandbox": {
    "enabled": true,
    "v8Isolate": true
  }
}
```

## Isolation by Loading Mode

| Loading Mode | Isolation Level | Description | Best For |
|--------------|-----------------|-------------|----------|
| `in-process` | None | Plugin runs in main process | Core plugins, trusted code |
| `worker` | Process | Dedicated worker process | Most plugins (default) |
| `process` | Container | Docker container with sandbox | Third-party plugins |
| `wasm` | VM | WebAssembly in isolated runtime | Maximum security |

## Resource Limits

Resource limits are enforced differently by isolation level:

| Resource | Process | Container | VM |
|-----------|---------|-----------|-----|
| Memory | `setrlimit(RLIMIT_AS)` | cgroups | Firecracker config |
| CPU time | `setrlimit(RLIMIT_CPU)` | cpuset cgroup | vCPU count |
| Storage | Disk quota | Volume size | Disk image size |
| Network | None (use OS) | iptables rules | Firecracker network |
| Processes | N/A (single) | PID namespace | Separate VM |

### Memory Limits

Memory limits include both RSS and swap. When exceeded:
1. Plugin receives `MemoryError` on allocation
2. After grace period (5s), process is terminated
3. Health status marked as `degraded` then `error`

### CPU Time Limits

CPU time is wall-clock + user + sys time. When exceeded:
1. `SIGTERM` sent to plugin process
2. After 5s grace period, `SIGKILL`
3. Crash report generated with stack traces

### File System Access

By default, plugins can access:
- Plugin installation directory (read-only)
- Plugin data directory: `~/.mekong/plugins/data/{plugin-id}/` (read-write)
- Temporary directory: `/tmp/mekong-plugin-{pid}` (read-write)

Additional paths require explicit permission:
```json
"permissions": {
  "file": ["read:/etc/mekong/*", "write:/var/log/mekong/*"]
}
```

## Sandbox Configuration

### Allowed/Blocked Modules

For Python plugins, you can restrict which modules can be imported:

```json
"sandbox": {
  "allowedModules": ["os", "pathlib", "logging", "json", "requests"],
  "blockedModules": ["subprocess", "socket", "ctypes", "multiprocessing"]
}
```

If `allowedModules` is specified, only those modules are permitted. If omitted but `blockedModules` is present, all modules except blocked ones are allowed.

**Note**: Module restrictions apply at import time. Dynamically loaded modules (via `importlib`) are also checked.

### Network Policies

```json
"sandbox": {
  "allowedHosts": [
    "https://api.example.com",
    "https://*.mekong.dev"
  ]
}
```

Network requests to non-allowed hosts are blocked at the proxy layer (intercepting `urllib`, `requests`, `httpx`).

## IPC Mechanism

Plugins communicate with the core via stdio JSON-RPC:

### Request Format
```json
{
  "jsonrpc": "2.0",
  "id": "req-123",
  "method": "command.execute",
  "params": {
    "command": "my-command",
    "args": ["arg1", "arg2"],
    "kwargs": {"option": "value"}
  }
}
```

### Response Format
```json
{
  "jsonrpc": "2.0",
  "id": "req-123",
  "result": {
    "success": true,
    "output": "Command completed",
    "data": {...}
  }
}
```

### Error Format
```json
{
  "jsonrpc": "2.0",
  "id": "req-123",
  "error": {
    "code": -32000,
    "message": "Plugin execution failed",
    "data": {
      "type": "RuntimeError",
      "traceback": "..."
    }
  }
}
```

## Lifecycle and Isolation

### Startup

1. Core spawns plugin process based on `loadingMode`
2. Plugin initialization happens in isolated context
3. Health check runs to verify isolation working
4. Plugin registers commands/hooks

### Execution

1. Command invocation routed to plugin via IPC
2. Input validation against manifest permissions
3. Resource tracking begins
4. Timeout enforced based on `resources.cpuTime`
5. Output captured and returned

### Shutdown

1. Graceful shutdown: `stop()` called, SIGTERM sent
2. Force shutdown after 10s: SIGKILL
3. Orphan cleanup: core reaps any remaining child processes
4. Health status updated

## Debugging Isolation Issues

### Check Plugin Process

```bash
# Find plugin process
ps aux | grep mekong-plugin

# Check resource limits
cat /proc/{pid}/limits

# View cgroup membership (containers)
cat /proc/{pid}/cgroup
```

### Enable Debug Logging

```bash
export MEKONG_PLUGIN_DEBUG=1
export MEKONG_ISOLATION_VERBOSE=1
```

### Common Issues

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `ImportError: blocked module` | Module in `blockedModules` | Add to `allowedModules` or remove from `blockedModules` |
| `PermissionError: file access denied` | Missing file permission | Add `file:read:path` to `permissions` |
| `Plugin killed` | Memory limit exceeded | Increase `resources.memory` or optimize plugin |
| `Connection refused` | Network blocked | Add host to `sandbox.allowedHosts` |
| `TimeoutError` | CPU time limit | Increase `resources.cpuTime` |

## Performance Considerations

| Isolation Level | Startup Time | Memory Overhead | Command Latency |
|-----------------|--------------|-----------------|-----------------|
| in-process | <10ms | 0MB | baseline |
| worker | ~100ms | 50MB | +10-20ms |
| process | ~300ms | 100MB | +20-50ms |
| wasm | ~500ms | 200MB | +50-100ms |

## Security Best Practices

1. **Always use isolation**: Never run `in-process` for third-party plugins
2. **Least privilege**: Grant only necessary permissions
3. **Review dependencies**: Audit plugin dependencies for vulnerabilities
4. **Monitor resources**: Use health monitoring to detect abuse
5. **Sign verified plugins**: Use plugin signatures for marketplace trust

## See Also

- [Plugin Security Hardening](./plugin-security-hardening.md)
- [Plugin Manifest Format](./plugin-manifest-format.md)
- [Plugin API Specification](./plugin-api-specification.md)
