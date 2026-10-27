from services import parse_positive_int, parse_weight


def test_parse_weight_valid_float():
    assert parse_weight("135.5") == 135.5


def test_parse_weight_valid_int_like_float_returns_int():
    assert parse_weight("135.0") == 135
    assert isinstance(parse_weight("135.0"), int)


def test_parse_weight_rejects_zero_or_negative():
    assert parse_weight("0") is None
    assert parse_weight("-10") is None


def test_parse_weight_rejects_non_numeric():
    assert parse_weight("abc") is None
    assert parse_weight(None) is None


def test_parse_positive_int_valid():
    assert parse_positive_int("8") == 8


def test_parse_positive_int_rejects_zero_or_negative():
    assert parse_positive_int("0") is None
    assert parse_positive_int("-3") is None


def test_parse_positive_int_rejects_non_numeric():
    assert parse_positive_int("abc") is None
    assert parse_positive_int(None) is None
