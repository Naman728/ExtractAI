"""Unit tests for batch address normalization and limits."""

from app.services.batch_service import normalize_addresses


def test_normalize_addresses_dedupes_and_strips():
    out = normalize_addresses(
        [
            "  Albany, GA 31705, USA ",
            "Albany, GA 31705, USA",
            "",
            "13020 SW Archer Road, Archer, FL 32618",
            "   ",
        ]
    )
    assert out == [
        "Albany, GA 31705, USA",
        "13020 SW Archer Road, Archer, FL 32618",
    ]


def test_normalize_keeps_commas_inside_address():
    out = normalize_addresses(
        [
            "1203 Cordele Rd, Albany, GA 31705, USA",
            "16 Computer Drive East, Albany, NY 12205",
        ]
    )
    assert len(out) == 2
    assert out[0] == "1203 Cordele Rd, Albany, GA 31705, USA"
    assert "Albany" not in out  # must not split city into its own row


def test_normalize_json_array_blob():
    out = normalize_addresses(
        [
            '["1203 Cordele Rd, Albany, GA 31705, USA", '
            '"16 Computer Drive East, Albany, NY 12205"]'
        ]
    )
    assert out == [
        "1203 Cordele Rd, Albany, GA 31705, USA",
        "16 Computer Drive East, Albany, NY 12205",
    ]


def test_normalize_strips_wrapping_quotes():
    out = normalize_addresses(['"4166 Lower Saucon Road, Hellertown, PA 18055-3322"'])
    assert out == ["4166 Lower Saucon Road, Hellertown, PA 18055-3322"]
