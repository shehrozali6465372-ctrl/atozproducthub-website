"""Rollback automation validation (Task 24 Phase I)."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_rollback_drill_script_exists_and_parses() -> None:
    script = ROOT / "tools/deploy/rollback-test.sh"
    assert script.exists()
    assert script.stat().st_mode & 0o111
    subprocess.run(["bash", "-n", str(script)], check=True, capture_output=True)


def test_rollback_drill_covers_required_steps() -> None:
    text = (ROOT / "tools/deploy/rollback-test.sh").read_text()
    for marker in (
        'deploy_tag "$PREV_TAG"',
        'deploy_tag "$NEXT_TAG"',
        "controlled failure",
        "execute rollback",
        "post-rollback verification",
        "database compatibility checks",
        "idempotency",
    ):
        assert marker in text, marker


def test_rollback_docs_define_db_safety_boundary() -> None:
    doc = (ROOT / "docs/operations/004-deployment-and-rollback.md").read_text()
    assert "forward-compatible" in doc
    assert "never downgrades" in doc.lower() or "rollback-safe by policy" in doc
    assert "release window" in doc


def test_migration_gate_script_exists() -> None:
    script = ROOT / "tools/db/validate-migrations.sh"
    assert script.exists()
    subprocess.run(["bash", "-n", str(script)], check=True, capture_output=True)
