import json
import os
import sys
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402

from reinvent26 import api  # noqa: E402
from mock.events_api import load_sample_catalog, start_server  # noqa: E402


@pytest.fixture()
def mock_api(monkeypatch):
    server = start_server(load_sample_catalog(), closed=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setattr(api, "BASE_URL",
                        f"http://127.0.0.1:{server.server_address[1]}")
    yield server
    server.shutdown()


def test_favorite_round_trip_with_schedule_confirm(mock_api):
    body = api.favorite_sessions("reinvent2026", "test-token", ["ant301-a"])
    assert body[0]["result"]["successful"] == ["ant301-a"]
    sched = api.get_schedule("reinvent2026", "test-token")
    assert sched["schedule"]["favorites"] == ["ant301-a"]
    assert api.remove_favorite("reinvent2026", "test-token", "ant301-a") is True
    assert api.remove_favorite("reinvent2026", "test-token", "ant301-a") is False
    sched = api.get_schedule("reinvent2026", "test-token")
    assert sched["schedule"]["favorites"] == []


def test_closed_gate_409s_reserve_and_cancel(mock_api):
    with pytest.raises(api.EventsError) as exc:
        api.reserve_sessions("reinvent2026", "test-token", ["ant301-a"])
    assert exc.value.status == 409
    mock_api.mock_state.closed = False
    try:
        body = api.reserve_sessions("reinvent2026", "test-token", ["ant301-a"])
        assert body[0]["result"]["successful"] == ["ant301-a"]
        sched = api.get_schedule("reinvent2026", "test-token")
        assert sched["schedule"]["reserved"] == ["ant301-a"]
        assert api.cancel_reservation("reinvent2026", "test-token", "ant301-a") is True
        sched = api.get_schedule("reinvent2026", "test-token")
        assert sched["schedule"]["reserved"] == []
    finally:
        mock_api.mock_state.closed = True


def test_personal_time_round_trip(mock_api):
    api.add_personal_time("reinvent2026", "test-token", "Lunch",
                          "2026-12-01T12:00:00", "2026-12-01T13:00:00",
                          description="Lunch")
    sched = api.get_schedule("reinvent2026", "test-token")
    blocks = sched["schedule"]["personalTime"]
    assert len(blocks) == 1 and blocks[0]["title"] == "Lunch"
    bid = blocks[0]["personalTimeId"]
    api.replace_personal_time("reinvent2026", "test-token", bid, "Lunch",
                              "2026-12-01T12:00:00", "2026-12-01T13:30:00",
                              description="Lunch")
    sched = api.get_schedule("reinvent2026", "test-token")
    assert sched["schedule"]["personalTime"][0]["endDateTime"] == \
        "2026-12-01T13:30:00"
    assert api.delete_personal_time("reinvent2026", "test-token", bid) is True
    sched = api.get_schedule("reinvent2026", "test-token")
    assert sched["schedule"]["personalTime"] == []


def test_writes_need_a_token(mock_api):
    with pytest.raises(api.EventsError) as exc:
        api.favorite_sessions("reinvent2026", None, ["ant301-a"])
    assert exc.value.status == 401
