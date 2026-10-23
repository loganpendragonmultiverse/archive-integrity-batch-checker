import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from archive_integrity_batch_checker.cli import main
from archive_integrity_batch_checker.core import analyze, render_json, render_markdown


def make_input(tmp_path: Path, outcome: str) -> tuple[Path, Path]:
    archive = tmp_path / "example.zip"
    if outcome == "invalid":
        archive.write_bytes(b"not a zip")
    else:
        with zipfile.ZipFile(archive, "w") as handle:
            if outcome != "warning":
                handle.writestr("page.txt", b"12345678")
    data = {"paths": [str(archive)]}
    if outcome == "incomplete":
        data["max_member_bytes"] = 4
    source = tmp_path / "input.json"
    source.write_text(json.dumps(data), encoding="utf-8")
    return source, archive


@pytest.mark.parametrize("outcome", ["clean", "invalid", "incomplete", "warning"])
@pytest.mark.parametrize(
    "policies",
    [[], ["invalid"], ["incomplete"], ["warning"], ["invalid", "warning"], ["warning", "warning"]],
)
def test_selected_exit_policy_retains_complete_report_and_inputs(
    tmp_path, capsys, outcome, policies
):
    source, archive = make_input(tmp_path, outcome)
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (source, archive)}
    args = [str(source), "--format", "json"]
    for policy in policies:
        args.extend(["--fail-on", policy])
    selected = set(policies)
    expected = int(
        (outcome in {"invalid", "incomplete"} and "invalid" in selected)
        or (outcome == "incomplete" and "incomplete" in selected)
        or (outcome == "warning" and "warning" in selected)
    )
    assert main(args) == expected
    captured = capsys.readouterr()
    assert captured.err == ""
    report = analyze(json.loads(source.read_text()))
    assert captured.out == render_json(report)
    assert report["version"] == 1
    assert {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in before} == before


@pytest.mark.parametrize("format", ["json", "markdown"])
def test_policy_failure_writes_report_before_returning_one(tmp_path, capsys, format):
    source, _ = make_input(tmp_path, "invalid")
    output = tmp_path / "new-report.txt"
    args = [str(source), "--fail-on", "invalid", "--format", format, "--output", str(output)]
    assert main(args) == 1
    report = analyze(json.loads(source.read_text()))
    expected = render_json(report) if format == "json" else render_markdown(report)
    assert output.read_text(encoding="utf-8") == expected
    assert capsys.readouterr().out == ""
    assert main(args) == 2
    assert output.read_text(encoding="utf-8") == expected
    assert "already exists" in capsys.readouterr().err


def test_operational_error_takes_precedence_and_unknown_policy_is_rejected(tmp_path, capsys):
    source = tmp_path / "invalid-input.json"
    source.write_text('{"paths":[]}', encoding="utf-8")
    assert main([str(source), "--fail-on", "invalid"]) == 2
    assert "paths" in capsys.readouterr().err
    with pytest.raises(SystemExit) as exc:
        main([str(source), "--fail-on", "anything"])
    assert exc.value.code == 2


def test_missing_archive_is_invalid_but_not_budget_incomplete(tmp_path, capsys):
    source = tmp_path / "missing.json"
    source.write_text(json.dumps({"paths": [str(tmp_path / "missing.zip")]}), encoding="utf-8")
    assert main([str(source), "--fail-on", "invalid", "--format", "json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["invalid_count"] == 1 and report["incomplete_count"] == 0
    assert main([str(source), "--fail-on", "incomplete", "--format", "json"]) == 0
