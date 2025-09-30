"""Tests for the CLI entry point selection logic."""

from pathlib import Path
import sys

import pytest

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
    assert input_dir == Path("data/new_input")
    assert output_dir == Path("results/new_output")


def test_main_legacy_flag_invokes_legacy(monkeypatch):
    """The --legacy flag should route execution through the legacy pipeline."""

    run_called = False
    captured = {}

    def fake_run_yaml(*_args, **_kwargs):  # pragma: no cover - should be skipped
        nonlocal run_called
        run_called = True
        return 0

    def fake_legacy(*, input_dir, output_dir, target_size):
        captured["args"] = (input_dir, output_dir, target_size)
        return 5

    monkeypatch.setattr(cli, "run_yaml_pipeline", fake_run_yaml)
    monkeypatch.setattr(cli, "main_legacy", fake_legacy)

    exit_code = cli.main(["--legacy", "--input-dir", "custom/in", "--output-dir", "custom/out"])

    assert exit_code == 5
    assert run_called is False

    input_dir, output_dir, target_size = captured["args"]
    assert input_dir == Path("custom/in")
    assert output_dir == Path("custom/out")
    assert target_size == cli.DCI_4K_RESOLUTION


def test_main_accepts_positional_input_override(monkeypatch, tmp_path):
    """Providing a single positional path should override the input directory."""

    captured = {}

    def fake_run_yaml(manifest_path, input_dir, output_dir):
        captured["args"] = (manifest_path, input_dir, output_dir)
        return 0

    def fail_legacy(*_args, **_kwargs):  # pragma: no cover - should not run
        raise AssertionError("Legacy path should not execute when --legacy is absent")

    monkeypatch.setattr(cli, "run_yaml_pipeline", fake_run_yaml)
    monkeypatch.setattr(cli, "main_legacy", fail_legacy)

    custom_input = tmp_path / "assets"

    exit_code = cli.main([str(custom_input)])

    assert exit_code == 0
    _, input_dir, output_dir = captured["args"]
    assert input_dir == custom_input
    assert output_dir == Path("results/new_output")


def test_main_accepts_positional_input_and_output_for_legacy(monkeypatch, tmp_path):
    """Two positional paths should override input and output for the legacy pipeline."""

    captured = {}

    def fake_run_yaml(*_args, **_kwargs):  # pragma: no cover - skip YAML path
        raise AssertionError("YAML pipeline should not run when --legacy is provided")

    def fake_legacy(*, input_dir, output_dir, target_size):
        captured["args"] = (input_dir, output_dir, target_size)
        return 0

    monkeypatch.setattr(cli, "run_yaml_pipeline", fake_run_yaml)
    monkeypatch.setattr(cli, "main_legacy", fake_legacy)

    custom_input = tmp_path / "assets"
    custom_output = tmp_path / "processed"

    exit_code = cli.main([
        "--legacy",
        str(custom_input),
        str(custom_output),
    ])

    assert exit_code == 0
    input_dir, output_dir, target_size = captured["args"]
    assert input_dir == custom_input
    assert output_dir == custom_output
    assert target_size == cli.DCI_4K_RESOLUTION


def test_main_rejects_mixed_input_sources():
    """Mixing --input-dir with a positional override should exit with an error."""

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--input-dir", "from-flag", "positional/input"])

    assert excinfo.value.code == 2


def test_main_rejects_mixed_output_sources():
    """Mixing --output-dir with a positional override should exit with an error."""

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--legacy", "--output-dir", "from-flag", "in_pos", "out_pos"])

    assert excinfo.value.code == 2
