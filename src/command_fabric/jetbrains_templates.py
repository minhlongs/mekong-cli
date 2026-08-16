# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""JetBrains plugin template generators for command fabric."""

from __future__ import annotations

from src.command_fabric.catalog import CommandRecord


def action_id(record: CommandRecord) -> str:
    """Return a stable JetBrains action id for one command."""
    normalized = "".join(part.title() for part in record.name.replace("_", "-").split("-"))
    return f"Mekong{normalized}Action"


def _escape_xml(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _escape_kotlin(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def plugin_xml(records: list[CommandRecord]) -> str:
    """Return a JetBrains plugin descriptor with generated command actions."""
    actions = "\n".join(
        (
            f'    <action id="{action_id(record)}" '
            f'class="com.mekong.commandfabric.MekongCommandAction" '
            f'text="Mekong: {_escape_xml(record.name)}" '
            f'description="{_escape_xml(record.description or record.name)}">'
            f'\n      <add-to-group group-id="ToolsMenu" anchor="last"/>'
            f"\n    </action>"
        )
        for record in records
    )
    return f"""<idea-plugin>
  <id>com.mekong.commandfabric</id>
  <name>Mekong Command Fabric</name>
  <vendor>Mekong</vendor>
  <description>Portable Mekong commands generated from command fabric.</description>
  <depends>com.intellij.modules.platform</depends>
  <actions>
{actions}
  </actions>
</idea-plugin>
"""


def build_gradle_kts() -> str:
    """Return a minimal Gradle build for a JetBrains Platform plugin."""
    return """plugins {
    id("org.jetbrains.intellij") version "1.17.4"
    kotlin("jvm") version "1.9.24"
}

group = "com.mekong"
version = "0.0.0"

repositories {
    mavenCentral()
}

intellij {
    version.set("2024.1")
    type.set("IC")
}

kotlin {
    jvmToolchain(17)
}
"""


def action_kt(records: list[CommandRecord]) -> str:
    """Return a generic JetBrains action class backed by command metadata."""
    entries = ",\n".join(
        (
            f'            "{action_id(record)}" to MekongCommand('
            f'"{_escape_kotlin(record.name)}", '
            f'"{_escape_kotlin(record.execution)}", '
            f'"{_escape_kotlin(record.argument_hint)}")'
        )
        for record in records
    )
    return f"""package com.mekong.commandfabric

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.ActionManager
import com.intellij.openapi.ui.Messages
import com.intellij.execution.configurations.GeneralCommandLine
import com.intellij.execution.process.OSProcessHandler
import com.intellij.execution.process.ProcessTerminatedListener
import com.intellij.execution.ui.RunContentExecutor

data class MekongCommand(
    val name: String,
    val execution: String,
    val argumentHint: String,
)

class MekongCommandAction : AnAction() {{
    override fun actionPerformed(event: AnActionEvent) {{
        val actionId = ActionManager.getInstance().getId(this) ?: return
        val command = COMMANDS[actionId] ?: return
        val args = Messages.showInputDialog(
            event.project,
            command.argumentHint.ifBlank {{ "Optional arguments" }},
            "Mekong: ${{command.name}}",
            Messages.getQuestionIcon(),
        ) ?: ""
        val argv = buildArgv(command.execution, splitArgs(args))
        val project = event.project ?: return
        val commandLine = GeneralCommandLine(argv)
            .withWorkDirectory(project.basePath)
        val handler = OSProcessHandler(commandLine)
        ProcessTerminatedListener.attach(handler)
        RunContentExecutor(project, handler)
            .withTitle("Mekong: ${{command.name}}")
            .run()
    }}

    companion object {{
        private fun buildArgv(execution: String, args: List<String>): List<String> {{
            val argv = mutableListOf<String>()
            var usedPlaceholder = false
            for (part in splitArgs(execution)) {{
                if (part == "$" + "ARGUMENTS") {{
                    argv.addAll(args)
                    usedPlaceholder = true
                }} else {{
                    argv.add(part)
                }}
            }}
            if (!usedPlaceholder) {{
                argv.addAll(args)
            }}
            return argv
        }}

        private fun splitArgs(value: String): List<String> {{
            val args = mutableListOf<String>()
            val current = StringBuilder()
            var inQuote = false
            for (ch in value) {{
                when {{
                    ch == '"' -> inQuote = !inQuote
                    ch.isWhitespace() && !inQuote -> {{
                        if (current.isNotEmpty()) {{
                            args.add(current.toString())
                            current.clear()
                        }}
                    }}
                    else -> current.append(ch)
                }}
            }}
            if (current.isNotEmpty()) {{
                args.add(current.toString())
            }}
            return args
        }}

        private val COMMANDS: Map<String, MekongCommand> = mapOf(
{entries}
        )
    }}
}}
"""


__all__ = ["action_id", "action_kt", "build_gradle_kts", "plugin_xml"]
