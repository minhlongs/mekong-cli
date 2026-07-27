// ── INJECTION CODE for session-init.cjs ──────────────────────────────────
// Paste this block BEFORE the line:
//   if (sessionStateEnabled && (source === 'startup' || source === 'compact')) {

// BEGIN INJECTION
if (source === 'compact') {
  try {
    var handoffPath = path.join(process.cwd(), '.claude', 'agent-memory', 'pre-compact-handoff.json');
    if (fs.existsSync(handoffPath)) {
      var handoff = JSON.parse(fs.readFileSync(handoffPath, 'utf8'));
      var pending = (handoff.todos || []).filter(function(t) { return t.status !== 'completed'; }).slice(0, 10);
      var done = (handoff.completedTodos || []).slice(-5);
      if (pending.length || done.length) {
        console.log('\n## Handoff (Pre-Compact Snapshot)\n');
        if (done.length) {
          console.log('### Done (dont redo):');
          done.forEach(function(t) {
            console.log('  - [x] ' + (t.content || t.id || 'task').substring(0, 80));
          });
        }
        if (pending.length) {
          console.log('### Pending (continue here):');
          pending.forEach(function(t) {
            console.log('  - [ ] ' + (t.content || t.id || 'task').substring(0, 80));
          });
        }
        console.log('\n_Branch: ' + (handoff.branch || '?') + ' | SHA: ' + (handoff.sha || '?') + ' | Dirty: ' + (handoff.dirtyFiles || 0) + ' files_\n');
      }
    }
  } catch { /* fail-open */ }
}
// END INJECTION
