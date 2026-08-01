import os, re

ROOT = "/Users/macbook/mekong-cli"
EXT = {".md", ".json", ".yaml", ".yml", ".cjs", ".js", ".txt", ".sh", ".py"}

TARGETS = [
    os.path.join(ROOT, ".claude"),
    os.path.join(ROOT, "CLAUDE.md"),
]

REPLACEMENTS = [
    ('/mk:cook', '/mk:cook'),
    ('/mk:fix', '/mk:fix'),
    ('/mk:brainstorm', '/mk:brainstorm'),
    ('/mk:plan', '/mk:plan'),
    ('/mk:scout', '/mk:scout'),
    ('/mk:advise', '/mk:advise'),
    ('/mk:debug', '/mk:debug'),
    ('/mk:code-review', '/mk:code-review'),
    ('/mk:docs', '/mk:docs'),
    ('/mk:project-management', '/mk:project-management'),
    ('/mk:git', '/mk:git'),
    ('/mk:journal', '/mk:journal'),
    ('/mk:preview', '/mk:preview'),
    ('/mk:team', '/mk:team'),
    ('/mk:compact', '/mk:compact'),
    ('/mk:remember', '/mk:remember'),
    ('/mk:save', '/mk:save'),
    ('/mk:techdebt', '/mk:techdebt'),
    ('/mk:marketing', '/mk:marketing'),
    ('/mk:idea', '/mk:idea'),
    ('/mk:context-engineering', '/mk:context-engineering'),
    ('/mk:find-skills', '/mk:find-skills'),
    ('/mk:docs-manager', '/mk:docs-manager'),
    ('/mk:review', '/mk:review'),
    ('/mk:docs-seeker', '/mk:docs-seeker'),
    ('/mk:ai-multimodal', '/mk:ai-multimodal'),
    ('/mk:sequential-thinking', '/mk:sequential-thinking'),
    ('/mk:project-organization', '/mk:project-organization'),
    ('/mk:skill-creator', '/mk:skill-creator'),
    # catch‑all: any remaining /mk: or /mk- that are not part of the /mk:cook line
]

changed_files = []
skipped = []

for base in TARGETS:
    if os.path.isfile(base):
        files = [base]
    else:
        files = []
        for root, dirs, fnames in os.walk(base):
            for fn in fnames:
                ext = os.path.splitext(fn)[1].lower()
                if ext in EXT:
                    files.append(os.path.join(root, fn))

    for fp in files:
        try:
            text = open(fp, encoding="utf-8", errors="ignore").read()
        except Exception as e:
            skipped.append((fp, str(e)))
            continue
        new = text
        for old, rep in REPLACEMENTS:
            if old in new:
                new = new.replace(old, rep)
if '/mk:' in new or '/mk-' in new:
    new = new.replace('/mk-', '/mk:')
    new = new.replace('/mk:', '/mk:')
            try:
                open(fp, "w", encoding="utf-8").write(new)
                changed_files.append(fp)
            except Exception as e:
                skipped.append((fp, str(e)))

print(f"Files changed: {len(changed_files)}")
for fp in changed_files:
    print(f"  {fp}")
if skipped:
    print(f"Skipped: {len(skipped)}")
    for fp, err in skipped[:5]:
        print(f"  {fp}: {err}")
