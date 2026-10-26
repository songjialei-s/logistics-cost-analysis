import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from src.demo_snapshot import canonical_csv_bytes, snapshot_hash, verify_snapshot, CSV_NAMES
ROOT = Path(__file__).resolve().parents[1]

class SnapshotTest(unittest.TestCase):
    def test_crlf_bom_and_lf_serialize_identically(self):
        lf = 'id,note\n1,"demo, only"\n2,合成\n'.encode("utf-8")
        windows = b"\xef\xbb\xbf" + lf.replace(b"\n", b"\r\n")
        self.assertEqual(canonical_csv_bytes(windows), lf)
        self.assertEqual(canonical_csv_bytes(lf), lf)
        self.assertEqual(snapshot_hash(canonical_csv_bytes(windows)), snapshot_hash(lf))

    def test_round_trip_preserves_csv_field_values(self):
        import csv, io
        raw = b'id,note\r\n1,"quoted ""demo"""\r\n2,"line1\r\nline2"\r\n'
        before = list(csv.reader(io.StringIO(raw.decode(), newline="")))
        after = list(csv.reader(io.StringIO(canonical_csv_bytes(raw).decode(), newline="")))
        self.assertEqual(before, after)
        self.assertEqual(canonical_csv_bytes(canonical_csv_bytes(raw)), canonical_csv_bytes(raw))

    def test_fixed_snapshot_and_manifest(self):
        manifest = verify_snapshot(ROOT / "data/demo")
        self.assertEqual(manifest["rows"], {"charges":144, "parcels":72, "rejected":18})
        self.assertEqual(manifest["expected"]["total_cost_cny"], 7947)

    def test_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            for name in (*CSV_NAMES, "manifest.json"):
                shutil.copyfile(ROOT / "data/demo" / name, target / name)
            p = target / "charges.csv"
            p.write_bytes(p.read_bytes().replace(b"DEMO-1-1-1", b"DEMO-9-1-1", 1))
            with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                verify_snapshot(target)

    def test_git_clean_filter_preserves_snapshot_bytes(self):
        git = shutil.which("git")
        if not git:
            self.skipTest("Git unavailable")
        if not (ROOT / ".git").exists():
            self.skipTest("Downloaded ZIP: local LF/hash tests still apply")
        env = os.environ.copy()
        env["GIT_OPTIONAL_LOCKS"] = "0"
        for name in CSV_NAMES:
            relative = "data/demo/" + name
            payload = (ROOT / relative).read_bytes()
            raw = subprocess.check_output([git, "--no-optional-locks", "-C", str(ROOT),
                "hash-object", "--no-filters", "--stdin"], input=payload, env=env)
            attrs = subprocess.check_output([git, "--no-optional-locks", "-C", str(ROOT),
                "check-attr", "eol", "--", relative], env=env).decode()
            self.assertTrue(attrs.strip().endswith(": lf"))
            for autocrlf in ("true", "false", "input"):
                with self.subTest(file=name, autocrlf=autocrlf):
                    cleaned = subprocess.check_output([git, "--no-optional-locks", "-C", str(ROOT),
                        "-c", "core.autocrlf=" + autocrlf, "hash-object", "--path=" + relative,
                        "--stdin"], input=payload, env=env)
                    self.assertEqual(cleaned, raw, "Git would change CSV bytes")

