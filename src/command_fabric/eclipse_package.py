"""Generate an Eclipse plugin scaffold from command fabric records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.command_fabric.adapters import export_adapter_manifest
from src.command_fabric.catalog import CommandRecord, build_command_catalog, export_command_catalog


@dataclass(frozen=True)
class EclipsePackageArtifact:
    """One generated Eclipse package artifact."""

    name: str
    path: str


def plugin_xml(records: list[CommandRecord]) -> str:
    """Return Eclipse plugin.xml with generated commands."""
    command_entries = "\n".join(
        f'      <command id="com.mekong.commandfabric.{record.name}" name="Mekong: {record.name}"/>'
        for record in records
    )
    handler_entries = "\n".join(
        (
            f'      <handler commandId="com.mekong.commandfabric.{record.name}" '
            'class="com.mekong.commandfabric.MekongCommandHandler"/>'
        )
        for record in records
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<plugin>
   <extension point="org.eclipse.ui.commands">
{command_entries}
   </extension>
   <extension point="org.eclipse.ui.handlers">
{handler_entries}
   </extension>
</plugin>
"""


def pom_xml() -> str:
    """Return a minimal Maven/Tycho build scaffold."""
    return """<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.mekong</groupId>
  <artifactId>command-fabric-eclipse</artifactId>
  <version>0.0.0-SNAPSHOT</version>
  <packaging>eclipse-plugin</packaging>
  <properties>
    <tycho.version>4.0.7</tycho.version>
  </properties>
</project>
"""


def _escape_java(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def handler_java(records: list[CommandRecord]) -> str:
    """Return a generic Eclipse handler backed by command metadata."""
    entries = ",\n".join(f'        COMMANDS.put("{record.name}", "{_escape_java(record.execution)}");' for record in records)
    return f"""package com.mekong.commandfabric;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;

public final class MekongCommandHandler extends AbstractHandler {{
    private static final Map<String, String> COMMANDS = new HashMap<>();

    static {{
{entries}
    }}

    @Override
    public Object execute(ExecutionEvent event) throws ExecutionException {{
        String commandId = event.getCommand().getId();
        String name = commandId.substring(commandId.lastIndexOf('.') + 1);
        String execution = COMMANDS.get(name);
        if (execution == null) {{
            throw new ExecutionException("Unknown Mekong command: " + name);
        }}
        try {{
            new ProcessBuilder(buildArgv(execution, Collections.emptyList())).start();
        }} catch (IOException error) {{
            throw new ExecutionException("Failed to run Mekong command", error);
        }}
        return null;
    }}

    private static List<String> buildArgv(String execution, List<String> args) {{
        List<String> argv = new ArrayList<>();
        boolean usedPlaceholder = false;
        for (String part : splitArgs(execution)) {{
            if ("$ARGUMENTS".equals(part)) {{
                argv.addAll(args);
                usedPlaceholder = true;
            }} else {{
                argv.add(part);
            }}
        }}
        if (!usedPlaceholder) {{
            argv.addAll(args);
        }}
        return argv;
    }}

    private static List<String> splitArgs(String value) {{
        List<String> args = new ArrayList<>();
        StringBuilder current = new StringBuilder();
        boolean inQuote = false;
        for (int index = 0; index < value.length(); index++) {{
            char ch = value.charAt(index);
            if (ch == '"') {{
                inQuote = !inQuote;
            }} else if (Character.isWhitespace(ch) && !inQuote) {{
                if (current.length() > 0) {{
                    args.add(current.toString());
                    current.setLength(0);
                }}
            }} else {{
                current.append(ch);
            }}
        }}
        if (current.length() > 0) {{
            args.add(current.toString());
        }}
        return args;
    }}
}}
"""


def _write(path: Path, content: str) -> EclipsePackageArtifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return EclipsePackageArtifact(path.name, path.as_posix())


def materialize_eclipse_package(
    output_dir: Path,
    records: list[CommandRecord] | None = None,
) -> dict[str, object]:
    """Write an Eclipse plugin scaffold."""
    command_records = records if records is not None else build_command_catalog()
    artifacts = [
        _write(output_dir / "plugin.xml", plugin_xml(command_records)),
        _write(output_dir / "pom.xml", pom_xml()),
        _write(output_dir / "src" / "com" / "mekong" / "commandfabric" / "MekongCommandHandler.java", handler_java(command_records)),
        _write(output_dir / "data" / "canonical.json", json.dumps(export_command_catalog(command_records), indent=2) + "\n"),
        _write(output_dir / "data" / "eclipse.json", json.dumps(export_adapter_manifest("eclipse", command_records), indent=2) + "\n"),
        _write(output_dir / "README.md", "# Mekong Eclipse\n\nEclipse plugin scaffold generated from Mekong command fabric.\n"),
        _write(output_dir / "BUILD.md", "# Build\n\nBuild with Eclipse PDE or Tycho, then install into Eclipse dropins.\n"),
    ]
    return {
        "schema": "mekong.command_fabric.eclipse_package.v1",
        "output_dir": output_dir.as_posix(),
        "command_count": len(command_records),
        "artifact_count": len(artifacts),
        "artifacts": [artifact.__dict__ for artifact in artifacts],
    }


__all__ = ["EclipsePackageArtifact", "handler_java", "materialize_eclipse_package", "plugin_xml", "pom_xml"]
