"""Package-manager template bodies for Mekong CLI distribution."""

from __future__ import annotations

import json


def homebrew_formula(command_count: int) -> str:
    return f"""class MekongCli < Formula
  desc "Mekong command fabric CLI with {command_count} command definitions"
  homepage "https://github.com/longtho638-jpg/mekong-cli"
  url "https://github.com/longtho638-jpg/mekong-cli/archive/refs/tags/v0.0.0.tar.gz"
  sha256 "PLACEHOLDER_SHA256"
  license "BSL-1.1"

  depends_on "python@3.12"

  def install
    libexec.install Dir["*"]
    bin.write_exec_script libexec/"scripts/mekong-wrapper.sh"
  end

  test do
    system "#{{bin}}/mekong", "--help"
  end
end
"""


def scoop_manifest(command_count: int) -> str:
    return json.dumps(
        {
            "version": "0.0.0",
            "description": f"Mekong command fabric CLI with {command_count} command definitions.",
            "homepage": "https://github.com/longtho638-jpg/mekong-cli",
            "license": "BSL-1.1",
            "url": "https://github.com/longtho638-jpg/mekong-cli/releases/download/v0.0.0/mekong-windows-x64.zip",
            "hash": "PLACEHOLDER_SHA256",
            "bin": "mekong.exe",
            "checkver": {"github": "https://github.com/longtho638-jpg/mekong-cli"},
            "autoupdate": {
                "url": "https://github.com/longtho638-jpg/mekong-cli/releases/download/v$version/mekong-windows-x64.zip"
            },
        },
        indent=2,
    ) + "\n"


def winget_manifest(command_count: int) -> str:
    return f"""PackageIdentifier: Mekong.MekongCLI
PackageVersion: 0.0.0
PackageLocale: en-US
Publisher: Mekong
PackageName: Mekong CLI
License: BSL-1.1
ShortDescription: Mekong command fabric CLI with {command_count} command definitions.
Installers:
  - Architecture: x64
    InstallerType: zip
    InstallerUrl: https://github.com/longtho638-jpg/mekong-cli/releases/download/v0.0.0/mekong-windows-x64.zip
    InstallerSha256: PLACEHOLDER_SHA256
ManifestType: singleton
ManifestVersion: 1.6.0
"""


def chocolatey_spec(command_count: int) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<package>
  <metadata>
    <id>mekong-cli</id>
    <version>0.0.0</version>
    <title>Mekong CLI</title>
    <authors>Mekong</authors>
    <licenseUrl>https://github.com/longtho638-jpg/mekong-cli/blob/main/LICENSE</licenseUrl>
    <projectUrl>https://github.com/longtho638-jpg/mekong-cli</projectUrl>
    <description>Mekong command fabric CLI with {command_count} command definitions.</description>
    <tags>mekong cli ai agent command-fabric</tags>
  </metadata>
</package>
"""


def nix_flake(command_count: int) -> str:
    return f"""{{
  description = "Mekong command fabric CLI with {command_count} command definitions";

  outputs = {{ self, nixpkgs }}:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in {{
      packages = forAllSystems (system:
        let pkgs = import nixpkgs {{ inherit system; }};
        in {{
          default = pkgs.python312Packages.buildPythonApplication {{
            pname = "mekong-cli";
            version = "0.0.0";
            src = self;
            format = "pyproject";
          }};
        }});
    }};
}}
"""


def aur_pkgbuild(command_count: int) -> str:
    return f"""pkgname=mekong-cli
pkgver=0.0.0
pkgrel=1
pkgdesc="Mekong command fabric CLI with {command_count} command definitions"
arch=('x86_64' 'aarch64')
url='https://github.com/longtho638-jpg/mekong-cli'
license=('BSL-1.1')
depends=('python')
source=("$pkgname-$pkgver.tar.gz::$url/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('PLACEHOLDER_SHA256')

package() {{
  cd "$srcdir/$pkgname-$pkgver"
  python -m installer --destdir="$pkgdir" dist/*.whl
}}
"""


def debian_control(command_count: int) -> str:
    return f"""Package: mekong-cli
Version: 0.0.0
Section: utils
Priority: optional
Architecture: all
Maintainer: Mekong <support@mekongmind.com>
Depends: python3
Description: Mekong command fabric CLI
 Mekong command fabric CLI with {command_count} command definitions.
"""


def rpm_spec(command_count: int) -> str:
    return f"""Name:           mekong-cli
Version:        0.0.0
Release:        1%{{?dist}}
Summary:        Mekong command fabric CLI
License:        BSL-1.1
URL:            https://github.com/longtho638-jpg/mekong-cli
Source0:        %{{name}}-%{{version}}.tar.gz
BuildArch:      noarch
Requires:       python3

%description
Mekong command fabric CLI with {command_count} command definitions.

%install
mkdir -p %{{buildroot}}%{{_bindir}}
install -m 0755 scripts/mekong-wrapper.sh %{{buildroot}}%{{_bindir}}/mekong

%files
%{{_bindir}}/mekong
"""


__all__ = [
    "aur_pkgbuild",
    "chocolatey_spec",
    "debian_control",
    "homebrew_formula",
    "nix_flake",
    "rpm_spec",
    "scoop_manifest",
    "winget_manifest",
]
