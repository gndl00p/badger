from types import SimpleNamespace
from unittest.mock import MagicMock

from tests.fakes.display import FakeDisplay

import main


def _cfg_mod():
    return SimpleNamespace(
        NAME="P", TITLE="T", ORG="R", URL="u",
        CONTACT={}, BIO="b", BIO_SKILLS="s", NOW="n",
        WIFI_SSID="", WIFI_PSK="",
        AGGREGATOR_URL="", AGGREGATOR_TOKEN="", REFRESH_MINUTES=15,
    )


def test_dispatches_to_badge_mode(tmp_path, monkeypatch):
    p = tmp_path / "state.json"
    p.write_text('{"mode": "badge", "last_data": null}')

    badge_inst = MagicMock()
    desk_inst = MagicMock()
    monkeypatch.setattr(main, "_build_display", lambda: FakeDisplay())
    monkeypatch.setattr(main, "_load_config", _cfg_mod)
    monkeypatch.setattr(main, "BadgeMode", lambda d, c: badge_inst)
    monkeypatch.setattr(main, "DeskMode", lambda d, c, state_path: desk_inst)
    monkeypatch.setattr(main, "_poll_loop", lambda *a, **kw: None)

    main.run(state_path=str(p))

    badge_inst.render_current.assert_called_once()
    desk_inst.cycle.assert_not_called()


def test_dispatches_to_desk_mode(tmp_path, monkeypatch):
    p = tmp_path / "state.json"
    p.write_text('{"mode": "desk", "last_data": null}')

    badge_inst = MagicMock()
    desk_inst = MagicMock()
    monkeypatch.setattr(main, "_build_display", lambda: FakeDisplay())
    monkeypatch.setattr(main, "_load_config", _cfg_mod)
    monkeypatch.setattr(main, "BadgeMode", lambda d, c: badge_inst)
    monkeypatch.setattr(main, "DeskMode", lambda d, c, state_path: desk_inst)
    monkeypatch.setattr(main, "_poll_loop", lambda *a, **kw: None)

    main.run(state_path=str(p))

    desk_inst.cycle.assert_called_once()
    badge_inst.render_current.assert_not_called()
