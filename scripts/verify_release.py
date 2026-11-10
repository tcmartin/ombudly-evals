"""Offline integrity and score verification; no writes or network calls."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
import score


def main():
    manifest = json.loads((ROOT / "MANIFEST.json").read_text())
    for name, digest in manifest["files_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    runs = json.loads((ROOT / "results/index.json").read_text())
    count = 0
    for entry in runs:
        directory = ROOT / "results" / entry["run"]
        suite = entry["suite"]
        keys = ROOT / "evals" / (suite if suite != "v1" else "") / "answer_keys"
        rows = []
        for path in sorted(directory.glob("*.raw.json")):
            raw = json.loads(path.read_text())
            key = json.loads((keys / (raw["household"] + ".json")).read_text())
            rows.append(score.score_household(raw, key))
        report = json.loads((directory / "report.json").read_text())
        assert rows == report["households"], entry["run"]
        assert score.aggregate(rows) == report["aggregate"] == entry["aggregate"], entry["run"]
        assert len(rows) == entry["households"] == entry["expected_households"], entry["run"]
        count += len(rows)
    print(f"PASS: {len(manifest['files_sha256'])} file hashes, {len(runs)} runs, {count} household scores and aggregates")


if __name__ == "__main__":
    main()
