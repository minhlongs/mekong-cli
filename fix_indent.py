import re
with open("src/mekongcli/core/goal_engine/service.py") as fh:
    content = fh.read()
lines = content.split("
")
fixed = []
in_class = False
for line in lines:
    stripped = line.lstrip()
    if stripped.startswith("class GoalEngine:"):
        in_class = True
        fixed.append(line)
    elif in_class and stripped and not line.startswith("    ") and not stripped.startswith("#") and not stripped.startswith(""""") and not stripped.startswith("from ") and not stripped.startswith("import ") and not stripped.startswith("def _mirror") and not stripped.startswith("memory_store") and not stripped.startswith("errors") and not stripped.startswith("try") and not stripped.startswith("except") and not stripped.startswith("self.") and not stripped.startswith("if") and not stripped.startswith("return") and not stripped.startswith("status") and not stripped.startswith("goal") and not stripped.startswith("goal_id") and not stripped.startswith("task_id") and not stripped.startswith("label") and not stripped.startswith("state") and not stripped.startswith("kind") and not stripped.startswith("content_str"):
        if not stripped:
            fixed.append(line)
        else:
            fixed.append("    " + line)
    else:
        fixed.append(line)
with open("src/mekongcli/core/goal_engine/service.py", "w") as fh:
    fh.write("
".join(fixed))
