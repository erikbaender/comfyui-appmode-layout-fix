import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/apply-comfy-appmode-fix.py"
spec = importlib.util.spec_from_file_location("installer", SCRIPT)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.root = self.base / "instance with spaces" / "ComfyUI"
        self.root.mkdir(parents=True)
        (self.root / "custom_nodes").mkdir()
        (self.root / "main.py").write_text("")
        (self.root / "nodes.py").write_text('WEB_DIRECTORY = "web"\nNODE_CLASS_MAPPINGS = {}\n')
        (self.root / "server.py").write_text("EXTENSION_WEB_DIRS = {}\n")
        self.target = self.root / "custom_nodes" / "appmode_layout_fix"

    def tearDown(self):
        self.temporary.cleanup()

    def test_cli_accepts_parent_root_and_custom_nodes(self):
        for directory in (self.root.parent, self.root, self.root / "custom_nodes"):
            result = subprocess.run([sys.executable, str(SCRIPT), str(directory)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.target / "__init__.py").read_bytes(), Path(__file__).resolve().parents[1].joinpath("__init__.py").read_bytes())
        self.assertEqual((self.target / "web/js/appmode_layout_fix.js").read_bytes(), Path(__file__).resolve().parents[1].joinpath("web/js/appmode_layout_fix.js").read_bytes())

    def test_rerun_does_not_rewrite_files(self):
        installer.install(self.root)
        before = {p: p.stat().st_mtime_ns for p in self.target.rglob("*") if p.is_file()}
        installer.install(self.root)
        self.assertEqual(before, {p: p.stat().st_mtime_ns for p in before})

    def test_preserves_modified_extension(self):
        installer.install(self.root)
        file = self.target / "__init__.py"
        file.write_text("# Local customization\n")
        with self.assertRaisesRegex(ValueError, "differs"):
            installer.install(self.root)
        self.assertEqual(file.read_text(), "# Local customization\n")

    def test_incomplete_instance_is_not_created(self):
        missing = self.base / "not-installed"
        result = subprocess.run([sys.executable, str(SCRIPT), str(missing)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(missing.exists())

    def test_registry_discovers_complete_instances_and_deduplicates(self):
        second = self.base / "second" / "ComfyUI"
        second.mkdir(parents=True)
        for name in ("main.py", "nodes.py", "server.py"):
            (second / name).write_text((self.root / name).read_text())
        (second / "custom_nodes").mkdir()
        registry = self.base / "installations.json"
        registry.write_text(json.dumps([
            {"installPath": str(self.root.parent)},
            {"installPath": str(self.root)},
            {"installPath": str(self.base / "incomplete")},
            {"sourceId": "cloud", "remoteUrl": "https://cloud.comfy.org"},
            {"installPath": str(second.parent)},
        ]))
        self.assertEqual(installer.discover_roots(registry), [self.root, second])

    def test_unsupported_loader_is_not_modified(self):
        (self.root / "nodes.py").write_text("# An unsupported loader\n")
        with self.assertRaisesRegex(ValueError, "conventions"):
            installer.install(self.root)
        self.assertFalse(self.target.exists())

    def test_extension_symlink_is_not_followed(self):
        elsewhere = self.base / "unrelated"
        elsewhere.mkdir()
        self.target.symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            installer.install(self.root)
        self.assertEqual(list(elsewhere.iterdir()), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
