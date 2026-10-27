"""Portable integrity checks use isolated fixtures, never edit archived inputs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / "verify_transfer.py"
spec = importlib.util.spec_from_file_location("verify_transfer", SCRIPT)
transfer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transfer)


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.put("source/data.json", b'{"original":true}\n')
        self.code = transfer.SITE + "dist/assets/app.js"
        self.put(self.code, b"/* original code */\n")
        self.manifest = {"algorithm": "SHA-256", "files": [
            {"path": name, "bytes": len((self.root / name).read_bytes()),
             "sha256": hashlib.sha256((self.root / name).read_bytes()).hexdigest()}
            for name in ("source/data.json", self.code)
        ]}
        self.save_manifest()

    def put(self, name, contents):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
        return path

    def save_manifest(self):
        (self.root / "SHA256_MANIFEST.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def run_cli(self, *args):
        process = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root), *args],
                                 capture_output=True, text=True)
        self.assertEqual(process.stderr, "")
        return process.returncode, json.loads(process.stdout)

    def test_untouched_snapshot_passes(self):
        code, report = self.run_cli("--mode", "snapshot")
        self.assertEqual(code, 0)
        self.assertEqual(report["filesChecked"], 2)

    def test_same_size_data_corruption_fails(self):
        self.put("source/data.json", b'{"original":fals}\n')
        code, report = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("Changed: source/data.json", report["failures"])

    def test_missing_file_fails(self):
        (self.root / "source/data.json").unlink()
        code, report = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("Missing: source/data.json", report["failures"])

    def test_modified_code_is_reported_inputs_pass_snapshot_fails(self):
        self.put(self.code, b"/* maintained code */\n")
        code, report = self.run_cli()
        self.assertEqual(code, 0)
        change = report["historicalCodeChanges"][0]
        self.assertEqual(change["path"], self.code)
        self.assertNotEqual(change["originalSha256"], change["currentSha256"])
        self.assertEqual(self.run_cli("--mode", "snapshot")[0], 1)

    def test_missing_editable_code_still_fails(self):
        (self.root / self.code).unlink()
        self.assertEqual(self.run_cli()[0], 1)

    def test_git_and_python_cache_do_not_break_snapshot(self):
        self.put(".git/objects/de/adbeef", b"git object")
        self.put(".git/config", b"git config")
        self.put("06_Verification/__pycache__/verify_transfer.cpython-312.pyc", b"cache")
        code, report = self.run_cli("--mode", "snapshot")
        self.assertEqual(code, 0)
        self.assertEqual(report["addedFiles"], [])

    def test_local_virtual_environment_is_ignored(self):
        self.put(".venv/lib/python3.12/site-packages/dependency.py", b"# dependency")
        self.assertEqual(self.run_cli("--mode", "snapshot")[0], 0)

    def test_git_worktree_pointer_is_ignored(self):
        self.put(".git", b"gitdir: /outside/worktree\n")
        self.assertEqual(self.run_cli("--mode", "snapshot")[0], 0)

    def test_generated_output_must_be_explicit(self):
        self.put("build/check.json", b"{}")
        self.assertEqual(self.run_cli()[0], 1)
        code, report = self.run_cli("--allow-output", "build")
        self.assertEqual(code, 0)
        self.assertEqual(report["ignoredOutputs"], ["build/check.json"])

    def test_output_exception_cannot_hide_original_corruption(self):
        self.put("source/data.json", b"broken")
        self.assertEqual(self.run_cli("--allow-output", "source")[0], 1)

    def test_new_sources_are_visible_and_snapshot_rejects_them(self):
        name = transfer.SITE + "tests/test_new.py"
        self.put(name, b"# new test")
        code, report = self.run_cli()
        self.assertEqual(code, 0)
        self.assertEqual(report["addedFiles"], [name])
        self.assertEqual(self.run_cli("--mode", "snapshot")[0], 1)

    def test_unrecognized_new_data_fails(self):
        self.put(transfer.SITE + "dist/data/new.js", b"unreviewed source")
        self.assertEqual(self.run_cli()[0], 1)

    def test_unsafe_manifest_paths_fail(self):
        for path in ("../escape", "/tmp/escape", "C:/escape", "a\\b", "a/../b", "a//b", "./a", ".git/config", "a\x00b"):
            with self.subTest(path=path):
                self.manifest["files"][0]["path"] = path
                self.save_manifest()
                code, report = self.run_cli()
                self.assertEqual(code, 1)
                self.assertTrue(report["failures"][0].startswith("Invalid manifest:"))

    def test_duplicate_path_hash_size_and_algorithm_validation(self):
        original = json.loads(json.dumps(self.manifest))
        mutations = [lambda m: m["files"].append(m["files"][0]),
                     lambda m: m["files"][0].update(sha256="z" * 64),
                     lambda m: m["files"][0].update(bytes=True),
                     lambda m: m.update(algorithm="MD5"),
                     lambda m: m.update(files=[])]
        for mutate in mutations:
            self.manifest = json.loads(json.dumps(original))
            mutate(self.manifest)
            self.save_manifest()
            self.assertEqual(self.run_cli()[0], 1)

    def test_duplicate_json_keys_fail(self):
        (self.root / "SHA256_MANIFEST.json").write_text('{"algorithm":"SHA-256","algorithm":"MD5","files":[]}', encoding="utf-8")
        self.assertEqual(self.run_cli()[0], 1)

    def test_manifest_symlink_fails(self):
        original = self.root / "SHA256_MANIFEST.json"
        alternate = self.root / "manifest-copy.json"
        original.rename(alternate)
        original.symlink_to(alternate)
        self.assertEqual(self.run_cli()[0], 1)

    def test_historical_file_and_directory_symlinks_fail(self):
        original = self.root / "source/data.json"
        outside = self.root / "alternate.json"
        original.rename(outside)
        original.symlink_to(outside)
        self.assertEqual(self.run_cli()[0], 1)
        original.unlink()
        (self.root / "source").rmdir()
        alternate_dir = self.root / "alternate-dir"
        alternate_dir.mkdir()
        (alternate_dir / "data.json").write_bytes(outside.read_bytes())
        (self.root / "source").symlink_to(alternate_dir, target_is_directory=True)
        self.assertEqual(self.run_cli()[0], 1)

    def test_unmanifested_symlink_cannot_hide_in_output_exception(self):
        (self.root / "build").symlink_to(self.root / "source", target_is_directory=True)
        self.assertEqual(self.run_cli("--allow-output", "build")[0], 1)

    def test_invalid_manifest_json_is_structured_failure(self):
        (self.root / "SHA256_MANIFEST.json").write_text("{", encoding="utf-8")
        code, report = self.run_cli()
        self.assertEqual(code, 1)
        self.assertEqual(report["result"], "FAIL")

    def test_explicit_output_preserves_stdout_and_previous_evidence(self):
        output = self.root / "build/transfer.json"
        code, report = self.run_cli("--output", str(output))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.read_text()), report)
        before = output.read_bytes()
        self.assertEqual(self.run_cli("--output", str(output))[0], 1)
        self.assertEqual(output.read_bytes(), before)

    def test_output_cannot_replace_missing_historical_file(self):
        output = self.root / "source/data.json"
        output.unlink()
        self.assertEqual(self.run_cli("--output", str(output))[0], 1)
        self.assertFalse(output.exists())

    def test_output_cannot_replace_manifest(self):
        before = (self.root / "SHA256_MANIFEST.json").read_bytes()
        self.assertEqual(self.run_cli("--output", str(self.root / "SHA256_MANIFEST.json"))[0], 1)
        self.assertEqual((self.root / "SHA256_MANIFEST.json").read_bytes(), before)

    def test_invalid_output_exclusion_is_structured_failure(self):
        self.assertEqual(self.run_cli("--allow-output", "../outside")[0], 1)

    def test_invalid_archive_is_rejected_even_with_matching_hash(self):
        name = "source/workbook.xlsx"
        self.put(name, b"invalid zip")
        contents = (self.root / name).read_bytes()
        self.manifest["files"].append({"path": name, "bytes": len(contents), "sha256": hashlib.sha256(contents).hexdigest()})
        self.save_manifest()
        self.assertEqual(self.run_cli()[0], 1)

    def test_valid_archive_passes(self):
        name = "source/valid.xlsx"
        with zipfile.ZipFile(self.root / name, "w") as archive:
            archive.writestr("[Content_Types].xml", "<Types/>")
        contents = (self.root / name).read_bytes()
        self.manifest["files"].append({"path": name, "bytes": len(contents), "sha256": hashlib.sha256(contents).hexdigest()})
        self.save_manifest()
        self.assertEqual(self.run_cli()[0], 0)


if __name__ == "__main__":
    unittest.main()
