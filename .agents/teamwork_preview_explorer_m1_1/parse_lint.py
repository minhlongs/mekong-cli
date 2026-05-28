import re
from collections import defaultdict

file_path = "/Users/macbook/projects/sophia-ai-factory/apps/sophia-ai-factory/lint_output_new.txt"

with open(file_path, "r") as f:
    content = f.read()

# Regular expression to match ESLint format
# Matches something like:
# /path/to/file.ts
#   line:col  warning  message  rule-name
#
# But wait, looking at the log:
# /Users/macbook/projects/sophia-ai-factory/apps/sophia-ai-factory/src/app/[locale]/dashboard/account/account-billing-tab.tsx
#   51:5  warning  Error: Calling setState synchronously within an effect can trigger cascading renders
#
# And then:
# /Users/macbook/projects/sophia-ai-factory/apps/sophia-ai-factory/src/app/[locale]/dashboard/account/account-billing-tab.tsx:51:5
#   49 |
#   50 |   useEffect(() => {
# > 51 |     fetchHistory(filter).catch(() => setLoading(false));
#      |     ^^^^^^^^^^^^ Avoid calling setState() directly within an effect
#   52 |   }, [filter, fetchHistory]);
#   53 |
#   54 |   function formatAmount(cents: number) {  react-hooks/set-state-in-effect
#
# Another format:
# /Users/macbook/projects/sophia-ai-factory/apps/sophia-ai-factory/src/app/[locale]/dashboard/account/page.tsx
#   32:19  warning  '_locale' is assigned a value but never used  @typescript-eslint/no-unused-vars
#
# Let's write a simple parser.
# Split by lines.
lines = content.split('\n')
current_file = None
warnings = []

# Let's inspect line by line
i = 0
while i < len(lines):
    line = lines[i].strip()
    if not line:
        i += 1
        continue
    
    # Check if this line is an absolute file path starting with /Users
    if line.startswith("/Users/") and not (":" in line and (line.endswith(":") or re.search(r':\d+:\d+', line))):
        current_file = line
        i += 1
        continue
        
    # Check if this is a warning line
    # e.g., "51:5  warning  Error: Calling setState synchronously within an effect..."
    # or "32:19  warning  '_locale' is assigned a value but never used  @typescript-eslint/no-unused-vars"
    match = re.match(r'^(\d+):(\d+)\s+(warning|error)\s+(.*)$', line)
    if match:
        line_num = match.group(1)
        col_num = match.group(2)
        severity = match.group(3)
        msg_and_rule = match.group(4)
        
        # Extract rule if it is at the end of the line
        # ESLint rule names are like @typescript-eslint/no-unused-vars, react-hooks/set-state-in-effect, etc.
        # But wait! For react-hooks/set-state-in-effect, it doesn't show rule name on the same warning line.
        # It shows the rule name at the end of the code context lines:
        # "54 |   function formatAmount(cents: number) {  react-hooks/set-state-in-effect"
        # Let's search ahead for the rule name.
        rule = None
        # Let's look for standard rule name in the warning line first
        rule_match = re.search(r'\s+([@a-zA-Z0-9\-\/]+)$', msg_and_rule)
        if rule_match:
            rule = rule_match.group(1)
            # Remove rule from message
            msg = msg_and_rule[:rule_match.start()].strip()
        else:
            msg = msg_and_rule.strip()
            
        # If no rule was found, let's scan ahead to see if there is code context ending with a rule name
        if not rule or '/' not in rule:
            # Look ahead up to 15 lines for code blocks
            j = i + 1
            while j < len(lines) and j < i + 15:
                next_line = lines[j]
                if next_line.startswith("/Users/"):
                    break # hit next file or next section
                # If we see a rule at the end of a line with code context
                # E.g. "react-hooks/set-state-in-effect"
                for r in ["react-hooks/set-state-in-effect", "react-hooks/static-components", "react-hooks/purity", "react-hooks/immutability", "@next/next/no-img-element"]:
                    if r in next_line:
                        rule = r
                        break
                if rule:
                    break
                j += 1
        
        # Fallback if no rule is found
        if not rule:
            rule = "unknown-rule"
            
        warnings.append({
            "file": current_file,
            "line": line_num,
            "col": col_num,
            "severity": severity,
            "message": msg,
            "rule": rule
        })
    i += 1

# Print Summary by Rule
rule_counts = defaultdict(int)
file_counts = defaultdict(int)
rule_files = defaultdict(list)

for w in warnings:
    rule_counts[w["rule"]] += 1
    file_counts[w["file"]] += 1
    rule_files[w["rule"]].append(w)

print(f"Total Warnings parsed: {len(warnings)}")
print("\n--- Warnings by Rule ---")
for rule, count in sorted(rule_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"{rule}: {count}")

print("\n--- Top 15 Files with most warnings ---")
for f, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
    # Make path relative to apps/sophia-ai-factory
    rel_path = f.replace("/Users/macbook/projects/sophia-ai-factory/apps/sophia-ai-factory/", "")
    print(f"{rel_path}: {count}")

print("\n--- Detailed breakdown of react-hooks/ rules ---")
for rule in ["react-hooks/set-state-in-effect", "react-hooks/static-components", "react-hooks/purity", "react-hooks/immutability"]:
    items = rule_files.get(rule, [])
    print(f"\nRule: {rule} ({len(items)} items)")
    # Group by file
    f_group = defaultdict(list)
    for it in items:
        f_group[it["file"]].append(it)
    for f, its in sorted(f_group.items(), key=lambda x: len(x[1]), reverse=True):
        rel_path = f.replace("/Users/macbook/projects/sophia-ai-factory/apps/sophia-ai-factory/", "")
        lines_str = ", ".join(f"L{it['line']}" for it in its)
        print(f"  {rel_path}: {len(its)} times ({lines_str})")
