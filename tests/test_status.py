from tests.fakes.display import FakeDisplay

import status


def test_header_and_back_hint():
    d = FakeDisplay()
    status.render(d, "KLBB", updated_z="22:00")
    texts = " ".join(d.texts())
    assert "Status" in texts
    assert "B back" in texts


def test_station_and_updated_rendered():
    d = FakeDisplay()
    status.render(d, "KLBB", updated_z="22:00")
    texts = " ".join(d.texts())
    assert "KLBB" in texts
    assert "22:00Z" in texts


def test_no_updated_hides_last_line():
    d = FakeDisplay()
    status.render(d, "KLBB", updated_z=None)
    texts = " ".join(d.texts())
    # "Last:" only rendered when a timestamp is available
    assert "Last:" not in texts


def test_battery_label_usb(monkeypatch):
    monkeypatch.setattr(status, "_battery_v", lambda: 4.92)
    d = FakeDisplay()
    status.render(d, "KLBB", updated_z="22:00")
    texts = " ".join(d.texts())
    assert "Battery:" in texts
    assert "4.92V" in texts
    assert "USB" in texts


def test_battery_label_lipo(monkeypatch):
    monkeypatch.setattr(status, "_battery_v", lambda: 3.72)
    d = FakeDisplay()
    status.render(d, "KLBB", updated_z="22:00")
    texts = " ".join(d.texts())
    assert "3.72V" in texts
    assert "LiPo" in texts


def test_battery_label_unknown(monkeypatch):
    monkeypatch.setattr(status, "_battery_v", lambda: None)
    d = FakeDisplay()
    status.render(d, "KLBB", updated_z="22:00")
    texts = " ".join(d.texts())
    assert "Battery:" in texts
    assert "--" in texts


def test_wifi_connected_with_rssi(monkeypatch):
    monkeypatch.setattr(status, "_wifi_info", lambda: {"connected": True, "ip": "10.0.200.138", "rssi": -54})
    d = FakeDisplay()
    status.render(d, "KLBB", updated_z="22:00")
    texts = " ".join(d.texts())
    assert "-54 dBm" in texts
    assert "10.0.200.138" in texts


def test_wifi_disconnected(monkeypatch):
    monkeypatch.setattr(status, "_wifi_info", lambda: {"connected": False})
    d = FakeDisplay()
    status.render(d, "KLBB", updated_z="22:00")
    texts = " ".join(d.texts())
    assert "offline" in texts


def test_draws_header_divider():
    d = FakeDisplay()
    status.render(d, "KLBB", updated_z="22:00")
    lines = [args for name, args in d.calls if name == "line"]
    assert any(a[1] == 24 for a in lines)
