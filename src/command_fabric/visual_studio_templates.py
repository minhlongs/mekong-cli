# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Visual Studio VSIX template generators for command fabric."""

from __future__ import annotations

from src.command_fabric.catalog import CommandRecord


def _escape_csharp(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def vsix_manifest() -> str:
    """Return a minimal VSIX manifest."""
    return """<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
  <Metadata>
    <Identity Id="Mekong.CommandFabric.VisualStudio" Version="0.0.0" Language="en-US" Publisher="Mekong" />
    <DisplayName>Mekong Command Fabric</DisplayName>
    <Description xml:space="preserve">Visual Studio command bridge generated from Mekong command fabric.</Description>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Community" Version="[17.0,18.0)" />
  </Installation>
  <Prerequisites>
    <Prerequisite Id="Microsoft.VisualStudio.Component.CoreEditor" Version="[17.0,18.0)" DisplayName="Visual Studio core editor" />
  </Prerequisites>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.VsPackage" Path="MekongCommandFabric.pkgdef" />
  </Assets>
</PackageManifest>
"""


def csproj() -> str:
    """Return a minimal SDK-style C# project."""
    return """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net472</TargetFramework>
    <LangVersion>latest</LangVersion>
    <GeneratePkgDefFile>true</GeneratePkgDefFile>
    <IncludeAssemblyInVSIXContainer>true</IncludeAssemblyInVSIXContainer>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.VisualStudio.SDK" Version="17.9.37000" PrivateAssets="all" />
  </ItemGroup>
</Project>
"""


def package_cs(records: list[CommandRecord]) -> str:
    """Return a Visual Studio package entrypoint with generated command metadata."""
    entries = ",\n".join(
        f'            ["{record.name}"] = "{_escape_csharp(record.execution)}"' for record in records
    )
    return f"""using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading;
using Microsoft.VisualStudio.Shell;

namespace Mekong.CommandFabric.VisualStudio
{{
    [PackageRegistration(UseManagedResourcesOnly = true, AllowsBackgroundLoading = true)]
    [Guid("f866a992-28d3-44f3-9a66-6d3c63f7b381")]
    public sealed class MekongCommandFabricPackage : AsyncPackage
    {{
        internal static readonly IReadOnlyDictionary<string, string> Commands = new Dictionary<string, string>
        {{
{entries}
        }};

        protected override async System.Threading.Tasks.Task InitializeAsync(
            CancellationToken cancellationToken,
            IProgress<ServiceProgressData> progress)
        {{
            await JoinableTaskFactory.SwitchToMainThreadAsync(cancellationToken);
        }}

        internal static void Run(string name, string args)
        {{
            if (!Commands.TryGetValue(name, out var execution))
            {{
                throw new ArgumentException("Unknown Mekong command: " + name);
            }}
            var argv = BuildArgv(execution, SplitArgs(args ?? string.Empty));
            if (argv.Count == 0)
            {{
                throw new ArgumentException("Empty Mekong command invocation");
            }}
            var start = new ProcessStartInfo(argv[0])
            {{
                UseShellExecute = false,
                Arguments = string.Join(" ", argv.Skip(1).Select(QuoteArg)),
            }};
            Process.Start(start);
        }}

        private static IReadOnlyList<string> BuildArgv(string execution, IReadOnlyList<string> args)
        {{
            var argv = new List<string>();
            var usedPlaceholder = false;
            foreach (var part in SplitArgs(execution))
            {{
                if (part == "$ARGUMENTS")
                {{
                    argv.AddRange(args);
                    usedPlaceholder = true;
                }}
                else
                {{
                    argv.Add(part);
                }}
            }}
            if (!usedPlaceholder)
            {{
                argv.AddRange(args);
            }}
            return argv;
        }}

        private static IReadOnlyList<string> SplitArgs(string value)
        {{
            var args = new List<string>();
            var current = new System.Text.StringBuilder();
            var inQuote = false;
            foreach (var ch in value)
            {{
                if (ch == '"')
                {{
                    inQuote = !inQuote;
                }}
                else if (char.IsWhiteSpace(ch) && !inQuote)
                {{
                    if (current.Length > 0)
                    {{
                        args.Add(current.ToString());
                        current.Clear();
                    }}
                }}
                else
                {{
                    current.Append(ch);
                }}
            }}
            if (current.Length > 0)
            {{
                args.Add(current.ToString());
            }}
            return args;
        }}

        private static string QuoteArg(string value)
        {{
            if (value.Length == 0 || value.Any(char.IsWhiteSpace) || value.Contains("\\""))
            {{
                return "\\"" + value.Replace("\\\\", "\\\\\\\\").Replace("\\"", "\\\\\\"") + "\\"";
            }}
            return value;
        }}
    }}
}}
"""


__all__ = ["csproj", "package_cs", "vsix_manifest"]
