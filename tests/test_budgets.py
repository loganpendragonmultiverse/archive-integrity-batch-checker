import struct
import zipfile

import pytest

from archive_integrity_batch_checker.core import analyze


def archive(tmp_path, entries, compression=zipfile.ZIP_DEFLATED):
    path = tmp_path / "budget.zip"
    with zipfile.ZipFile(path, "w", compression=compression) as handle:
        for name, value in entries:
            handle.writestr(name, value)
    return path


def result(path, **limits):
    return analyze({"paths": [str(path)], **limits})["archives"][0]


def test_compressible_and_exact_limits(tmp_path):
    path = archive(tmp_path, [("a", b"x" * 100000)])
    assert result(path, max_member_bytes=100000, max_total_bytes=100000)["valid"]
    item = result(path, max_member_bytes=99)
    assert item["status"] == "incomplete" and not item["valid"]
    assert item["decompressed_bytes"] == 100
    assert not item["verification_complete"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["budget.zip"]


def test_total_budget_and_duplicate_occurrences(tmp_path):
    path = archive(tmp_path, [("a", b"123"), ("a", b"456")])
    assert result(path, max_total_bytes=6)["valid"]
    item = result(path, max_total_bytes=5)
    assert item["budget_exhausted"] == "max_total_bytes"
    assert item["duplicate_names"] == ["a"]
    assert analyze({"paths": [str(path)], "max_total_bytes": 5})["incomplete_count"] == 1


@pytest.mark.parametrize("key", ["max_member_bytes", "max_total_bytes"])
@pytest.mark.parametrize("value", [0, -1, True, 1.5, "10", None])
def test_invalid_budgets(key, value):
    with pytest.raises(ValueError, match="positive integer"):
        analyze({"paths": ["missing.zip"], key: value})


def test_crc_corruption_and_encryption(tmp_path):
    path = archive(tmp_path, [("a", b"abc")], zipfile.ZIP_STORED)
    original = path.read_bytes()
    changed = bytearray(original)
    changed[31] ^= 1
    path.write_bytes(changed)
    assert result(path)["error"] == "BadZipFile"
    changed = bytearray(original)
    central = changed.index(b"PK\x01\x02")
    struct.pack_into("<H", changed, 6, 1)
    struct.pack_into("<H", changed, central + 8, 1)
    path.write_bytes(changed)
    assert result(path)["error"] == "encrypted member"
    assert not result(path)["verification_complete"]


def test_size_and_unsupported_compression(tmp_path):
    path = archive(tmp_path, [("a", b"abc")], zipfile.ZIP_STORED)
    original = path.read_bytes()
    central = original.index(b"PK\x01\x02")
    changed = bytearray(original)
    struct.pack_into("<I", changed, central + 24, 4)
    path.write_bytes(changed)
    assert not result(path)["valid"]
    changed = bytearray(original)
    struct.pack_into("<H", changed, central + 10, 99)
    path.write_bytes(changed)
    assert result(path)["error"] == "NotImplementedError"


def test_malformed_lzma_is_a_batch_error(tmp_path):
    import lzma

    broken = tmp_path / "broken.zip"
    with zipfile.ZipFile(broken, "w", compression=zipfile.ZIP_LZMA) as handle:
        handle.writestr("a", b"hello world" * 100)
    content = bytearray(broken.read_bytes())
    central = content.index(b"PK\x01\x02")
    # Keep the LZMA header/properties intact and corrupt the compressed stream.
    content[40:central] = b"\xff" * (central - 40)
    broken.write_bytes(content)
    good = archive(tmp_path, [("a", b"safe")])
    report = analyze({"paths": [str(broken), str(good)], "max_member_bytes": 2000})
    assert report["archives"][0]["error"] == lzma.LZMAError.__name__
    assert report["archives"][0]["status"] == "error"
    assert not report["archives"][0]["verification_complete"]
    assert report["archives"][1]["valid"] and report["valid_count"] == 1
