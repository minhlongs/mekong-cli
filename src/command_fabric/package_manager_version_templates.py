"""Version-manager package templates for Mekong CLI."""

from __future__ import annotations


def asdf_plugin_readme(command_count: int) -> str:
    return f"""# asdf-mekong

asdf plugin scaffold for Mekong CLI with {command_count} command definitions.

## Install

```bash
asdf plugin add mekong https://github.com/longtho638-jpg/asdf-mekong.git
asdf install mekong latest
asdf global mekong latest
```
"""


def asdf_list_all() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail

git ls-remote --tags --refs https://github.com/longtho638-jpg/mekong-cli.git \
  | sed 's#.*refs/tags/v##' \
  | sort -V
"""


def asdf_download() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail

version="${ASDF_INSTALL_VERSION}"
download_path="${ASDF_DOWNLOAD_PATH}"
archive_url="https://github.com/longtho638-jpg/mekong-cli/archive/refs/tags/v${version}.tar.gz"

mkdir -p "${download_path}"
curl -fsSL "${archive_url}" | tar -xz --strip-components=1 -C "${download_path}"
"""


def asdf_install() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail

install_path="${ASDF_INSTALL_PATH}"
download_path="${ASDF_DOWNLOAD_PATH}"

mkdir -p "${install_path}"
cp -R "${download_path}/." "${install_path}/"
python3 -m pip install --prefix "${install_path}" "${install_path}"
mkdir -p "${install_path}/bin"
cat > "${install_path}/bin/mekong" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
MEKONG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${MEKONG_ROOT}"
python3 -m src.main "$@"
SH
chmod +x "${install_path}/bin/mekong"
"""


def mise_config(command_count: int) -> str:
    return f"""# Mekong CLI mise metadata with {command_count} command definitions.
# Publish this alongside GitHub releases so users can pin Mekong via mise.

[tools]
"github:longtho638-jpg/mekong-cli" = "latest"

[tasks.install-mekong]
description = "Install Mekong CLI from the checked-out release"
run = "python3 -m pip install ."
"""


__all__ = [
    "asdf_download",
    "asdf_install",
    "asdf_list_all",
    "asdf_plugin_readme",
    "mise_config",
]
