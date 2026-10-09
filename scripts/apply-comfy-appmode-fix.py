#!/usr/bin/env python3
"""Install the App Mode layout fix using Desktop's registry or an explicit path."""

import argparse
import json
import sys
import tempfile
from pathlib import Path


FILES = {
    "__init__.py": '''WEB_DIRECTORY = "./web/js"

NODE_CLASS_MAPPINGS = {}

__all__ = ["NODE_CLASS_MAPPINGS", "WEB_DIRECTORY"]
''',
    "web/js/appmode_layout_fix.js": '''import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "appmode.layout.fix",

    async setup() {
        const id = "appmode-layout-fix";

        if (document.getElementById(id)) {
            return;
        }

        const style = document.createElement("style");
        style.id = id;
        style.textContent = `
            nav.side-tool-bar-container + .p-splitter {
                min-width: 0 !important;
            }
        `;

        document.head.appendChild(style);
    },
});
''',
}


def find_root(directory):
    directory = directory.expanduser().resolve()
    candidates = [directory, directory / "ComfyUI"]
    if directory.name == "custom_nodes":
        candidates.insert(0, directory.parent)
    for candidate in candidates:
        if all((candidate / name).is_file() for name in ("main.py", "nodes.py", "server.py")) and (candidate / "custom_nodes").is_dir():
            return candidate
    raise ValueError(f"No complete ComfyUI instance found at {directory}. Finish installation first, or pass its actual directory.")


def discover_roots(registry):
    if not registry.is_file():
        raise ValueError(f"Desktop registry not found: {registry}. Pass your ComfyUI instance directory explicitly.")
    installations = json.loads(registry.read_text())
    if not isinstance(installations, list):
        raise ValueError(f"Unrecognized Desktop registry format: {registry}. Pass an instance directory explicitly.")
    roots = []
    for installation in installations:
        path = installation.get("installPath")
        if not isinstance(path, str) or not path:
            continue
        try:
            root = find_root(Path(path))
        except ValueError:
            print(f"Skipping incomplete instance: {path}", file=sys.stderr)
            continue
        if root not in roots:
            roots.append(root)
    if not roots:
        raise ValueError("No complete local ComfyUI instances found. Finish installation, then run this script again.")
    return roots


def install(root):
    nodes = (root / "nodes.py").read_text()
    server = (root / "server.py").read_text()
    if "WEB_DIRECTORY" not in nodes or "NODE_CLASS_MAPPINGS" not in nodes or "EXTENSION_WEB_DIRS" not in server:
        raise ValueError(f"Unrecognized frontend extension conventions in {root}; no files were changed there.")
    target = root / "custom_nodes" / "appmode_layout_fix"
    if target.is_symlink():
        raise ValueError(f"Refusing to overwrite a symlink: {target}")
    if target.exists():
        if target.is_dir() and all((target / name).is_file() and (target / name).read_bytes() == content.encode("utf-8") for name, content in FILES.items()):
            print(f"Already installed: {target}")
            return
        raise ValueError(f"Existing extension differs at {target}. Move it aside before rerunning; it has not been overwritten.")
    with tempfile.TemporaryDirectory(prefix=".appmode_layout_fix-", dir=target.parent) as temporary:
        staged = Path(temporary) / "extension"
        for name, content in FILES.items():
            file = staged / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(content, encoding="utf-8")
        staged.rename(target)
    print(f"Installed: {target}")


def main():
    parser = argparse.ArgumentParser(
        description="Apply the ComfyUI App Mode layout fix. With no path, find complete local instances in Comfy Desktop's registry.",
        epilog="Accepts an installation directory, its ComfyUI directory, or custom_nodes. Restart Comfy Desktop after installation. No downloads or extra dependencies are needed.",
    )
    parser.add_argument("directory", nargs="?", type=Path, help="ComfyUI instance directory (optional)")
    args = parser.parse_args()
    try:
        roots = [find_root(args.directory)] if args.directory else discover_roots(Path.home() / ".local/share/comfyui-desktop-2/installations.json")
    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    failed = False
    for root in roots:
        try:
            install(root)
        except (ValueError, OSError) as error:
            print(f"Error: {error}", file=sys.stderr)
            failed = True
    if not failed:
        print("Ready. Restart Comfy Desktop (or restart the backend and reload its frontend) to activate the fix.")
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
