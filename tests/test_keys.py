from identa.keys import (
    ACTION_ONBOARD,
    branch_name,
    canonical_json,
    idempotency_key,
    vendor_file_path,
)


def test_same_inputs_same_key() -> None:
    a = idempotency_key(1, ACTION_ONBOARD, {"name": "x", "domain": "y"})
    b = idempotency_key(1, ACTION_ONBOARD, {"domain": "y", "name": "x"})
    assert a == b
    assert len(a) == 64


def test_different_inputs_different_key() -> None:
    base = idempotency_key(1, ACTION_ONBOARD, {"name": "x"})
    assert base != idempotency_key(2, ACTION_ONBOARD, {"name": "x"})
    assert base != idempotency_key(1, "other", {"name": "x"})
    assert base != idempotency_key(1, ACTION_ONBOARD, {"name": "z"})


def test_company_id_type_does_not_change_key() -> None:
    assert idempotency_key(7, "a", {}) == idempotency_key("7", "a", {})


def test_canonical_json_is_compact_and_sorted() -> None:
    assert canonical_json({"b": 1, "a": [1, 2]}) == '{"a":[1,2],"b":1}'


def test_branch_and_file_names() -> None:
    key = "abcdef0123456789" * 4
    assert branch_name("vendor", 42, key) == "vendor/42-abcdef01"
    assert branch_name("crash-a", 42, key) == "crash-a/42-abcdef01"
    assert vendor_file_path(42) == "vendors/42.yaml"
