# Phase 2 Execution Guide

> Solo dev | Run each step, verify before next

---

## Step 0: Pre-flight Check
```bash
cd /Users/macbook/mekong-cli
git status --short | head -20
python3 -m src.main --help | head -5
ls -d src/core/binh_phap 2>/dev/null && echo FAIL || echo OK-not-yet-created
grep -rn "from src.binh_phap" src/ > /tmp/binh_phap_imports_before.txt
echo "Snapshot: /tmp/binh_phap_imports_before.txt"
```

## Step 1: Create new dirs
```bash
mkdir -p src/commercial src/finance src/research src/marketing src/observability src/governance src/core/binh_phap
for d in src/commercial src/finance src/research src/marketing src/observability src/governance src/core/binh_phap; do touch "$d/__init__.py"; done
```

## Step 2: Move topology.py
```bash
mv src/binh_phap/topology.py src/core/binh_phap/topology.py
```

## Step 3: Update imports
`src/core/binh_phap_dispatcher.py`: `from src.binh_phap.topology` -> `from src.core.binh_phap.topology`

`src/cli/binh_phap_commands.py`: `from src.binh_phap.topology` -> `from src.core.binh_phap.topology`
same for: `dag`, `executor`, `immortal_loop`, `reactions`, `recovery`, `operating_system`, `cto_daemon`

`src/cli/commands/commerce_status.py`: `from src.binh_phap.topology` -> `from src.core.binh_phap.topology`

## Step 4: Verify
```bash
python3 -m src.main --help
python3 -c "from src.core.binh_phap.topology import TopologyEngine; print('OK')"
```

## Rollback
```bash
git checkout -- src/
```
