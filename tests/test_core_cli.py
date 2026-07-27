import json
from pathlib import Path

import pytest

from archive_integrity_batch_checker.cli import main
from archive_integrity_batch_checker.core import PROJECT, analyze, render_json, render_markdown


def test_representative_sample_has_expected_result():
    data = json.loads(
        (Path(__file__).parents[1] / "examples" / "sample.json").read_text(encoding="utf-8")
    )
    report = analyze(data)
    assert report["version"] == 1 and report["project"] == PROJECT
    assert report["invalid_count"] == 1
    assert f'"project": "{PROJECT}"' in render_json(report)
    assert PROJECT.replace("-", " ").title() in render_markdown(report)


def test_missing_required_input_is_rejected():
    with pytest.raises(ValueError):
        analyze({})


def test_cli_json_and_output_safety(tmp_path, capsys):
    source = Path(__file__).parents[1] / "examples" / "sample.json"
    assert main([str(source), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["project"] == PROJECT
    output = tmp_path / "report.md"
    output.write_text("keep", encoding="utf-8")
    assert main([str(source), "--output", str(output)]) == 2


def test_valid_corrupt_and_unsupported_archives(tmp_path):
    import zipfile

    valid = tmp_path / "book.cbz"
    with zipfile.ZipFile(valid, "w") as archive:
        archive.writestr("001.txt", "page one")
        archive.writestr("002.txt", "page two")
    corrupt = tmp_path / "broken.epub"
    corrupt.write_bytes(b"not a zip")
    unsupported = tmp_path / "archive.rar"
    unsupported.write_bytes(b"rar")
    report = analyze({"paths": [str(valid), str(corrupt), str(unsupported)]})
    assert report["valid_count"] == 1
    assert report["invalid_count"] == 2
    assert report["archives"][0]["members"] == 2
    assert report["archives"][1]["error"] == "BadZipFile"
    assert report["archives"][2]["error"] == "unsupported archive family"
