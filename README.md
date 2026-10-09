# ComfyUI App Mode layout fix

A tiny frontend extension for the App Mode bug where a growing output gallery pushes the right-hand input panel off-screen. It injects this rule once when the frontend starts:

```css
nav.side-tool-bar-container + .p-splitter {
    min-width: 0 !important;
}
```

There are no backend nodes, dependencies, downloads at startup, or changes to ComfyUI's bundled frontend. ComfyUI loads the JavaScript through `WEB_DIRECTORY` automatically; no separate enable step is needed when custom extensions are allowed.

## Install

Choose either method below. Restart ComfyUI Desktop, or restart the backend and reload the frontend, after installation.

### Self-contained installer

Download or copy [`scripts/apply-comfy-appmode-fix.py`](scripts/apply-comfy-appmode-fix.py) into your scripts folder. It contains both extension files and only needs Python 3.

On Linux with ComfyUI Desktop's current instance registry:

```bash
python3 ~/Scripts/apply-comfy-appmode-fix.py
```

With no argument, the script reads `~/.local/share/comfyui-desktop-2/installations.json` and applies the fix to every complete local instance it finds. It skips incomplete installations and remote instances. Finish setting up a new instance before running it.

For a different Desktop registry layout or a standalone installation, provide the actual instance path:

```bash
python3 ~/Scripts/apply-comfy-appmode-fix.py "/path/to/ComfyUI"
```

The argument may be the ComfyUI root, its parent when it contains a `ComfyUI` directory, or its `custom_nodes` directory. The installer checks for the backend files and extension-loader markers before writing. It creates only `custom_nodes/appmode_layout_fix`; rerunning leaves matching files untouched and refuses to overwrite a different extension or a symlink.

The registry discovery is Linux-specific. An explicit path can be used wherever Python 3 and a compatible ComfyUI backend are available.

### Clone into custom_nodes

Find the `custom_nodes` directory belonging to your actual ComfyUI instance, then run:

```bash
git clone https://github.com/erikbaender/comfyui-appmode-layout-fix.git "/path/to/ComfyUI/custom_nodes/appmode_layout_fix"
```

Alternatively, copy `__init__.py` and `web/` from this repository into that directory. The required layout is:

```text
custom_nodes/appmode_layout_fix/
├── __init__.py
└── web/
    └── js/
        └── appmode_layout_fix.js
```

## Persistence and verification

The extension lives in the instance's `custom_nodes` directory and loads on each startup. Desktop updates that preserve that directory preserve the fix. A fresh instance or an update that replaces the instance requires installing it again; the standalone installer can be reused for this.

In the running frontend's developer console:

```javascript
document.querySelectorAll("style#appmode-layout-fix").length
// Expected: 1

document.getElementById("appmode-layout-fix")?.textContent
// Expected: the CSS rule shown above

getComputedStyle(document.querySelector("nav.side-tool-bar-container + .p-splitter")).minWidth
// Expected in App Mode with this selector present: "0px"
```

Enter App Mode before checking the splitter. Add outputs to the gallery and confirm the input panel stays within the viewport. Check backend logs and the browser console for extension loading errors if the style is missing. Custom extensions must not be disabled in ComfyUI.

The extension was verified on Fedora Linux with Desktop 1.1.3, ComfyUI 0.38.0, and frontend 1.53.6 on September 30, 2026. In the same frontend opened in a browser, the input panel's position and width stayed unchanged across 0, 12, and 60 output-history entries, including cached runs. Newer frontend layouts may use different selectors.

## Remove

After upgrading to an upstream fix, remove only `custom_nodes/appmode_layout_fix` from each instance where it was installed, then restart ComfyUI and reload the frontend. You may also delete the standalone installer from your scripts folder. No ComfyUI application files need restoring.

## Development

The installer embeds the extension so it can be copied independently. When changing the extension, update its embedded contents too. The tests check that installed files match the repository and cover repeat installation, path discovery, incomplete installations, conflicting files, and symlinks:

```bash
python3 -m unittest discover -s tests -v
```

## Upstream context

This packages the CSS workaround discussed in [frontend issue #14908](https://github.com/Comfy-Org/ComfyUI_frontend/issues/14908). Track [upstream pull request #15433](https://github.com/Comfy-Org/ComfyUI_frontend/pull/15433) for the underlying layout change. This is an unofficial local workaround.
