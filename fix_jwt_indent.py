from pathlib import Path

p = Path("src/auth/session_manager.py")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)

# Fix lines 67-84 (0-indexed 66-83): they have 1 leading space, need 4
for i in range(66, 84):
    line = lines[i]
    if line.strip():
        lines[i] = line[1:]           # drop the stray single space
        lines[i] = "    " + lines[i]  # prepend proper 4-space indent

p.write_text("".join(lines), encoding="utf-8")
print("OK")
