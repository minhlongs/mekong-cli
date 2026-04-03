use std::env;

use regex::Regex;

use crate::tools::PermissionLevel;

/// Permission enforcement mode
#[derive(Debug, Clone, PartialEq)]
pub enum PermissionMode {
    /// Ask for every write/execute (safest)
    Ask,
    /// Allow file edits, ask for bash (default)
    AllowEdits,
    /// Allow everything except deny list
    BypassPermissions,
}

/// Result of a permission check
#[derive(Debug)]
pub enum PermissionCheck {
    Allowed,
    Denied(String),
    NeedsApproval(String),
}

/// Guard that checks tool permissions before execution
pub struct PermissionGuard {
    mode: PermissionMode,
    deny_patterns: Vec<Regex>,
}

impl PermissionGuard {
    pub fn from_env() -> Self {
        let mode = match env::var("MEKONG_PERMISSION_MODE").as_deref() {
            Ok("bypass") => PermissionMode::BypassPermissions,
            Ok("ask") => PermissionMode::Ask,
            _ => PermissionMode::AllowEdits,
        };

        // Always-blocked patterns (even in bypass mode)
        let deny_patterns = vec![
            Regex::new(r"rm\s+-rf\s+/").unwrap(),
            Regex::new(r"sudo\s+rm").unwrap(),
            Regex::new(r"chmod\s+777").unwrap(),
            Regex::new(r"mkfs\.").unwrap(),
            Regex::new(r"dd\s+if=").unwrap(),
            Regex::new(r":\(\)\s*\{").unwrap(),
            Regex::new(r">\s*/dev/sd").unwrap(),
            Regex::new(r"curl.*\|\s*sh").unwrap(),
        ];

        Self { mode, deny_patterns }
    }

    /// Check if a tool execution is allowed given the current mode
    pub fn check(
        &self,
        tool_name: &str,
        level: &PermissionLevel,
        args: &str,
    ) -> PermissionCheck {
        // Deny list always blocks (even in bypass mode)
        if *level == PermissionLevel::Execute || *level == PermissionLevel::Dangerous {
            for pattern in &self.deny_patterns {
                if pattern.is_match(args) {
                    return PermissionCheck::Denied(format!(
                        "Blocked by deny rule: {}",
                        pattern.as_str()
                    ));
                }
            }
        }

        match (&self.mode, level) {
            // Read-only tools always allowed
            (_, PermissionLevel::ReadOnly) => PermissionCheck::Allowed,

            // Dangerous always needs confirmation
            (_, PermissionLevel::Dangerous) => {
                PermissionCheck::NeedsApproval(format!("Dangerous operation: {tool_name}"))
            }

            // AllowEdits: file writes ok, bash needs approval
            (PermissionMode::AllowEdits, PermissionLevel::WriteFile) => PermissionCheck::Allowed,
            (PermissionMode::AllowEdits, PermissionLevel::Execute) => {
                PermissionCheck::NeedsApproval(format!("Execute: {tool_name}"))
            }

            // Bypass: allow everything not denied
            (PermissionMode::BypassPermissions, _) => PermissionCheck::Allowed,

            // Ask: everything needs approval
            (PermissionMode::Ask, _) => {
                PermissionCheck::NeedsApproval(format!("{tool_name} requires approval"))
            }
        }
    }
}
