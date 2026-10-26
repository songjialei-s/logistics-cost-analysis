"""Canonical UTF-8/LF CSV snapshot integrity for the independent demo."""
import csv
import hashlib
import io
import json
from pathlib import Path
CSV_NAMES = ("charges.csv", "parcels.csv", "rejected.csv")

def canonical_csv_bytes(payload):
    """Normalize CSV serialization, preserving parsed field values."""
    source = io.StringIO(payload.decode("utf-8-sig"), newline="")
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(csv.reader(source))
    return output.getvalue().encode("utf-8")

def snapshot_hash(payload):
    return hashlib.sha256(payload).hexdigest()

def verify_snapshot(folder):
    folder = Path(folder)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8-sig"))
    if set(manifest["sha256"]) != set(CSV_NAMES):
        raise ValueError("Unexpected snapshot file list")
    for name in CSV_NAMES:
        payload = (folder / name).read_bytes()
        if payload != canonical_csv_bytes(payload):
            raise ValueError(f"CSV must be canonical UTF-8/LF: {name}")
        if snapshot_hash(payload) != manifest["sha256"][name]:
            raise ValueError(f"Snapshot SHA256 mismatch: {name}")
    return manifest

