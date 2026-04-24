from tests.fakes.display import FakeDisplay

from picker import render


def test_renders_all_stations_when_small_list():
    d = FakeDisplay()
    render(d, ["KLBB", "KAMA", "KDFW"], cursor=0, active_index=0)
    texts = " ".join(d.texts())
    assert "KLBB" in texts
    assert "KAMA" in texts
    assert "KDFW" in texts


def test_cursor_prefix_on_current_row():
    d = FakeDisplay()
    render(d, ["KLBB", "KAMA", "KDFW"], cursor=1, active_index=0)
    cursor_lines = [args[0] for name, args in d.calls if name == "text" and args[0].startswith("> KAMA")]
    assert cursor_lines


def test_active_suffix_on_selected_station():
    d = FakeDisplay()
    render(d, ["KLBB", "KAMA", "KDFW"], cursor=0, active_index=2)
    active_lines = [args[0] for name, args in d.calls if name == "text" and "KDFW *" in args[0]]
    assert active_lines


def test_cursor_and_active_can_be_same_row():
    d = FakeDisplay()
    render(d, ["KLBB", "KAMA"], cursor=0, active_index=0)
    lines = [args[0] for name, args in d.calls if name == "text" and args[0].startswith("> KLBB *")]
    assert lines


def test_scrolls_when_list_exceeds_visible():
    d = FakeDisplay()
    stations = ["K{0}".format(i).rjust(4, "X") for i in range(10)]
    render(d, stations, cursor=8, active_index=0)
    texts = " ".join(d.texts())
    # Cursor near the end → earliest stations scrolled off the top
    assert stations[8] in texts
    assert stations[0] not in texts


def test_pagination_hint_present_when_scrolling():
    d = FakeDisplay()
    stations = ["K{0:03d}".format(i) for i in range(10)]
    render(d, stations, cursor=3, active_index=0)
    texts = " ".join(d.texts())
    assert "4/10" in texts


def test_header_and_footer_hint_always_drawn():
    d = FakeDisplay()
    render(d, ["KLBB"], cursor=0, active_index=0)
    texts = " ".join(d.texts())
    assert "ICAO picker" in texts
    assert "A select" in texts
    assert "B back" in texts


def test_draws_header_divider_line():
    d = FakeDisplay()
    render(d, ["KLBB"], cursor=0, active_index=0)
    lines = [args for name, args in d.calls if name == "line"]
    assert any(a[1] == 14 for a in lines)
