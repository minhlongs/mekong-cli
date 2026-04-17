"""Tool registry — browser, file_system, execute."""

from agent_core.tools.browser import browse_website
from agent_core.tools.execute import execute_command
from agent_core.tools.file_system import OUTPUTS_DIR, read_file, write_file

REGISTRY = {
    "browse_website": browse_website,
    "read_file": read_file,
    "write_file": write_file,
    "execute_command": execute_command,
}

__all__ = [
    "REGISTRY",
    "OUTPUTS_DIR",
    "browse_website",
    "read_file",
    "write_file",
    "execute_command",
]
