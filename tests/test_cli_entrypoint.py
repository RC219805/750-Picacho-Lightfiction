"""Tests for the CLI entry point selection logic."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import main as cli


def test_main_defaults_to_yaml(monkeypatch):
    """Calling main([]) should run the YAML pipeline with default paths."""

    captured = {}

    def fake_run_yaml(manifest_path, input_dir, output_dir):
        captured["args"] = (manifest_path, input_dir, output_dir)
        return 0

    def fail_legacy():  # pragma: no cover - legacy should not run here
        raise AssertionError("Legacy path should not be used when no --legacy flag is provided")

    monkeypatch.setattr(cli, "run_yaml_pipeline", fake_run_yaml)
    monkeypatch.setattr(cli, "main_legacy", fail_legacy)

    exit_code = cli.main([])

    assert exit_code == 0
    manifest_path, input_dir, output_dir = captured["args"]
    assert manifest_path == Path("config/view_selects.yml")
    assert input_dir == Path("input")
    assert output_dir == Path("output")


def test_main_legacy_flag_invokes_legacy(monkeypatch):
    """The --legacy flag should route execution through the legacy pipeline."""

    run_called = False

    def fake_run_yaml(*_args, **_kwargs):  # pragma: no cover - should be skipped
        nonlocal run_called
        run_called = True
        return 0

    def fake_legacy():
        return 5

    monkeypatch.setattr(cli, "run_yaml_pipeline", fake_run_yaml)
    monkeypatch.setattr(cli, "main_legacy", fake_legacy)

    exit_code = cli.main(["--legacy"])

    assert exit_code == 5
    assert run_called is False
