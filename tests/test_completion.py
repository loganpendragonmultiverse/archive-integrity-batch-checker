import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from archive_integrity_batch_checker.cli import main
from archive_integrity_batch_checker.core import analyze


@pytest.mark.parametrize(
    "value", [None, [], "input", 1, True], ids=["null", "array", "text", "number", "bool"]
)
def test_root_shape(value):
    with pytest.raises(TypeError, match="JSON object"):
        analyze(value)


@pytest.mark.parametrize(
    "paths",
    ["archive.zip", {}, [], [None], [1], [True], [""], ["  "], ["bad\x00path"]],
    ids=["string", "object", "empty", "null", "number", "bool", "blank", "space", "nul"],
)
def test_path_shape(paths):
    with pytest.raises(ValueError, match="paths"):
        analyze({"paths": paths})


@pytest.mark.parametrize(
    "ratio",
    [True, None, "3", [], 0, -1, float("nan"), float("inf"), 10**400],
    ids=["bool", "null", "text", "array", "zero", "negative", "nan", "infinity", "overflow"],
)
def test_ratio_shape(ratio):
    with pytest.raises((TypeError, ValueError), match="finite positive"):
        analyze({"paths": ["missing.zip"], "max_compression_ratio": ratio})


def test_stat_failure_continues(tmp_path, monkeypatch):
    blocked = tmp_path / "blocked.zip"
    good = tmp_path / "good.zip"
    with ZipFile(good, "w") as archive:
        archive.writestr("page.txt", "page")
    original = Path.stat

    def stat(path, *args, **kwargs):
        if path == blocked:
            raise PermissionError("fixture")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", stat)
    report = analyze({"paths": [str(blocked), str(good)]})
    assert report["archives"][0]["error"] == "PermissionError"
    assert report["archives"][1]["valid"]
    assert report["valid_count"] == 1


def test_cli_invalid_root(tmp_path, capsys):
    source = tmp_path / "input.json"
    source.write_text("null")
    assert main([str(source)]) == 2
    assert "JSON object" in capsys.readouterr().err


@pytest.mark.parametrize("dangling", [False, True], ids=["existing-target", "dangling-target"])
def test_output_symlink_preserved(tmp_path, dangling):
    source = tmp_path / "input.json"
    source.write_text(json.dumps({"paths": ["missing.zip"]}))
    target = tmp_path / "target"
    if not dangling:
        target.write_text("valuable")
    output = tmp_path / "report.json"
    try:
        output.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symbolic links unavailable")
    assert main([str(source), "--output", str(output)]) == 2
    assert output.is_symlink()
    assert target.read_text() == "valuable" if not dangling else not target.exists()


def test_output_created_during_open_is_preserved(tmp_path, monkeypatch):
    source = tmp_path / "input.json"
    source.write_text(json.dumps({"paths": ["missing.zip"]}))
    output = tmp_path / "report.json"
    original = Path.open

    def raced(path, mode="r", *args, **kwargs):
        if path == output and mode == "x":
            with original(path, "w") as handle:
                handle.write("concurrent")
        return original(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", raced)
    assert main([str(source), "--output", str(output)]) == 2
    assert output.read_text() == "concurrent"


def test_markdown_filename_cannot_close_json_fence():
    from archive_integrity_batch_checker.core import render_markdown

    filename = "missing" + chr(10) + chr(96) * 3 + chr(10) + "INJECTED.zip"
    report = analyze({"paths": [filename]})
    rendered = render_markdown(report)
    assert chr(10) + "INJECTED.zip" not in rendered
    assert "INJECTED.zip" in rendered


@pytest.mark.parametrize("kind", ["version", "utf8"])
def test_unsupported_headers_continue_batch(tmp_path, kind):
    from zipfile import ZipInfo

    bad = tmp_path / "bad.zip"
    good = tmp_path / "good.zip"
    info = ZipInfo("page.txt")
    if kind == "version":
        info.extract_version = 99
        info.create_version = 99
    with ZipFile(bad, "w") as archive:
        archive.writestr(info, b"page")
    if kind == "utf8":
        payload = bytearray(bad.read_bytes())
        central = payload.index(b"PK" + bytes([1, 2]))
        payload[6:8] = (0x800).to_bytes(2, "little")
        payload[central + 8 : central + 10] = (0x800).to_bytes(2, "little")
        start = 0
        while True:
            at = payload.find(b"page.txt", start)
            if at < 0:
                break
            payload[at] = 255
            start = at + 8
        bad.write_bytes(payload)
    with ZipFile(good, "w") as archive:
        archive.writestr("page.txt", b"page")
    report = analyze({"paths": [str(bad), str(good)]})
    assert report["archives"][0]["status"] == "error"
    assert not report["archives"][0]["verification_complete"]
    assert report["archives"][0]["error"] == (
        "NotImplementedError" if kind == "version" else "UnicodeDecodeError"
    )
    assert report["archives"][1]["valid"]
