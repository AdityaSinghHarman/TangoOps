"""Smoke-tests poster/ui.py itself using Streamlit's AppTest framework.

This module exists because a real bug (DEFAULT_CATEGORY_KEY imported from
the wrong module) shipped and reached a live user before being caught —
none of the other test files ever actually import poster.ui, since it's
pure Streamlit UI code that a plain pytest import doesn't exercise the way
a running app does. AppTest runs the real render() function against a
simulated Streamlit session, which is what actually caught the bug.

Cannot drive st.file_uploader (unsupported by AppTest as of Streamlit
1.50.0), so this only covers page-load and widget-interaction — not a full
Generate click with real photos. poster_service/image pipeline correctness
is covered separately in test_poster_service.py / test_poster_demo_mode.py
with mocked participant images.
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

_PROBE_SCRIPT = """
from poster.ui import render
render(username="test@example.com", user_role="owner", business_id="biz_1", business_name="Test Biz")
"""


def _probe_path(tmp_path: Path) -> str:
    p = tmp_path / "_poster_ui_probe.py"
    p.write_text(_PROBE_SCRIPT)
    return str(p)


def test_poster_ui_module_imports_cleanly():
    import poster.ui  # noqa: F401 — the import itself is the assertion


def test_render_loads_without_exception(tmp_path):
    at = AppTest.from_file(_probe_path(tmp_path))
    at.run(timeout=30)
    assert not at.exception
    headers = [m.value for m in at.markdown]
    assert any("AI Poster Studio" in h for h in headers)
    assert any("Step 6" in h for h in headers)


def test_switching_every_category_does_not_crash(tmp_path):
    at = AppTest.from_file(_probe_path(tmp_path))
    at.run(timeout=30)
    assert not at.exception

    for label in [
        "Official Battle", "Finals / Competition", "Custom Poster",
        "Premium / Glam Birthday", "Battle Promotion", "Special Celebration",
        "Special Live Event", "Winner / Achievement", "Birthday Celebration",
    ]:
        at.selectbox(key="poster_category_select").select(label)
        at.run(timeout=30)
        assert not at.exception, f"switching to {label!r} raised: {at.exception}"


def test_demo_mode_defaults_on_when_no_provider_configured(tmp_path):
    at = AppTest.from_file(_probe_path(tmp_path))
    at.run(timeout=30)
    assert not at.exception
    assert at.checkbox(key="poster_demo_mode").value is True


def test_style_selection_does_not_crash(tmp_path):
    at = AppTest.from_file(_probe_path(tmp_path))
    at.run(timeout=30)
    at.selectbox(key="poster_style_select").select("Luxury Gold")
    at.run(timeout=30)
    assert not at.exception
