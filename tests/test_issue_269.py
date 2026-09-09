from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_planner_desktop_shares_grid_tracks_between_days():
    source = (ROOT / "static/meal-planner/style.css").read_text(encoding="utf-8")
    assert "grid-template-rows: auto repeat(2, minmax(118px, auto));" in source
    assert "grid-template-rows: subgrid;" in source
    assert "grid-row: span 3;" in source


def test_planner_mobile_keeps_vertical_layout_without_subgrid():
    source = (ROOT / "static/meal-planner/style.css").read_text(encoding="utf-8")
    assert ".planner-day { display: block; grid-template-rows: none; grid-row: auto; }" in source
