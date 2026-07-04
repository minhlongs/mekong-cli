from src.command_fabric.native_install import materialize_native_install


def test_native_install_writes_emacs_and_sublime_packages(tmp_path) -> None:
    target_root = tmp_path / "home"
    payload = materialize_native_install(
        tmp_path / "out",
        scope="project",
        hosts=["emacs", "sublime"],
        target_root=target_root,
        dry_run=False,
    )

    assert payload["install_count"] == 2
    assert (target_root / ".emacs.d" / "site-lisp" / "mekong-command-fabric" / "mekong-command-fabric.el").exists()
    assert (
        target_root
        / ".config"
        / "sublime-text"
        / "Packages"
        / "Mekong Command Fabric"
        / "mekong_command_fabric.py"
    ).exists()


def test_native_install_writes_vim_neovim_helix_and_zed_packages(tmp_path) -> None:
    target_root = tmp_path / "home"
    payload = materialize_native_install(
        tmp_path / "out",
        scope="project",
        hosts=["vim", "neovim", "helix", "zed"],
        target_root=target_root,
        dry_run=False,
    )

    assert payload["install_count"] == 4
    assert (
        target_root
        / ".vim"
        / "pack"
        / "mekong"
        / "start"
        / "command-fabric"
        / "plugin"
        / "mekong_command_fabric.vim"
    ).exists()
    assert (
        target_root
        / ".local"
        / "share"
        / "nvim"
        / "site"
        / "pack"
        / "mekong"
        / "start"
        / "command-fabric"
        / "lua"
        / "mekong.lua"
    ).exists()
    assert (target_root / ".config" / "helix" / "mekong-command-fabric" / "bin" / "mekong-helix").exists()
    assert (
        target_root
        / ".local"
        / "share"
        / "zed"
        / "extensions"
        / "installed"
        / "mekong-command-fabric"
        / "extension.toml"
    ).exists()


def test_native_install_writes_visual_studio_and_eclipse_packages(tmp_path) -> None:
    target_root = tmp_path / "home"
    payload = materialize_native_install(
        tmp_path / "out",
        scope="project",
        hosts=["visual-studio", "eclipse"],
        target_root=target_root,
        dry_run=False,
    )

    assert payload["install_count"] == 2
    assert (
        target_root
        / ".mekong"
        / "command-fabric"
        / "visual-studio"
        / "source.extension.vsixmanifest"
    ).exists()
    assert (target_root / "eclipse" / "dropins" / "mekong-command-fabric" / "plugin.xml").exists()


def test_native_install_writes_lightweight_editor_packages(tmp_path) -> None:
    target_root = tmp_path / "home"
    payload = materialize_native_install(
        tmp_path / "out",
        scope="project",
        hosts=["fleet", "nova", "lapce", "kakoune", "micro"],
        target_root=target_root,
        dry_run=False,
    )

    assert payload["install_count"] == 5
    assert (
        target_root
        / ".local"
        / "share"
        / "JetBrains"
        / "Fleet"
        / "plugins"
        / "mekong-command-fabric"
        / "plugin.json"
    ).exists()
    assert (
        target_root
        / "Library"
        / "Application Support"
        / "Nova"
        / "Extensions"
        / "mekong-command-fabric.novaextension"
        / "extension.js"
    ).exists()
    assert (target_root / ".local" / "share" / "lapce" / "plugins" / "mekong-command-fabric" / "lapce-plugin.toml").exists()
    assert (target_root / ".config" / "kak" / "autoload" / "mekong-command-fabric" / "kakrc").exists()
    assert (target_root / ".config" / "micro" / "plug" / "mekong-command-fabric" / "mekong.lua").exists()
