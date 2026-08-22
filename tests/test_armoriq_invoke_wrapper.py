import pytest

from app.armoriq.client import ArmorIQWrapperClient, HAS_OFFICIAL_SDK
from app.armoriq.errors import ArmorIQException


class DummyResult:
    def __init__(self, status=None, verified=None, result=None):
        self.status = status
        self.verified = verified
        self.result = result or {}


def make_wrapper_with_stub(invoke_return=None, invoke_exc=None):
    # Create a minimal wrapper instance by injecting a dummy client
    # Avoid requiring a real API key by setting a fake one for tests.
    wrapper = ArmorIQWrapperClient.__new__(ArmorIQWrapperClient)
    wrapper.api_key = "ak_test_dummy"
    wrapper.client = type("C", (), {})()
    if invoke_exc:
        def inv(**kwargs):
            raise invoke_exc
    else:
        def inv(**kwargs):
            return invoke_return

    wrapper.client.invoke = inv
    return wrapper


def test_invoke_allows_on_successful_result():
    r = DummyResult(status="success", verified=True)
    w = make_wrapper_with_stub(invoke_return=r)
    res = w.invoke(mcp="mcp", action="a", intent_token="t", params={})
    assert res.get("decision") == "ALLOW"


def test_invoke_blocks_on_error_result():
    r = DummyResult(status="error", verified=False)
    w = make_wrapper_with_stub(invoke_return=r)
    res = w.invoke(mcp="mcp", action="a", intent_token="t", params={})
    assert res.get("decision") == "BLOCK"


def test_invoke_blocks_on_malformed_result():
    # invoke returns None (malformed) -> should fail closed to BLOCK
    w = make_wrapper_with_stub(invoke_return=None)
    res = w.invoke(mcp="mcp", action="a", intent_token="t", params={})
    assert res.get("decision") == "BLOCK"


def test_invoke_maps_block_exception():
    # Simulate SDK PolicyBlockedException by raising a custom exception
    class BlockExc(Exception):
        pass

    w = make_wrapper_with_stub(invoke_exc=BlockExc("blocked"))
    # Unknown exception type should raise ArmorIQException (fail-closed)
    with pytest.raises(ArmorIQException):
        w.invoke(mcp="mcp", action="a", intent_token="t", params={})
