from datetime import date

from app.schemas.config import MenuConfig, MenuWeek
from app.services.menu import service as ms
from tests.helpers import set_config

H = {"Authorization": ""}


def week(name, **meals):
    days = [{}] * 7
    return {"name": name, "days": [dict(meals) for _ in range(7)]}


def test_rotation_follows_the_calendar():
    m = MenuConfig(weeks=[MenuWeek(), MenuWeek(), MenuWeek()], start_week=2, start_date="2026-10-19")
    # Monday 19 Oct 2026 starts week 2; the next Monday is week 3 and then week 1 again.
    assert ms.week_index(m, date(2026, 10, 19)) == 1
    assert ms.week_index(m, date(2026, 10, 25)) == 1
    assert ms.week_index(m, date(2026, 10, 26)) == 2
    assert ms.week_index(m, date(2026, 11, 2)) == 0
    assert ms.week_index(m, date(2026, 11, 9)) == 1
    # earlier dates count backwards through the cycle
    assert ms.week_index(m, date(2026, 10, 12)) == 0
    assert ms.week_index(m, date(2026, 10, 5)) == 2


def test_start_date_may_be_any_day_of_the_week_and_empty_means_this_week():
    m = MenuConfig(weeks=[MenuWeek(), MenuWeek()], start_week=2, start_date="2026-10-22")  # a Thursday
    assert ms.week_index(m, date(2026, 10, 19)) == 1
    assert ms.week_index(m, date(2026, 10, 26)) == 0
    assert ms.week_index(MenuConfig(weeks=[MenuWeek(), MenuWeek()], start_week=2), date(2026, 3, 4)) == 1
    assert ms.week_index(MenuConfig(), date(2026, 3, 4)) is None


def test_set_current_week_and_describe():
    m = MenuConfig(weeks=[MenuWeek(name="A"), MenuWeek(name="B"), MenuWeek(name="C")])
    m = ms.set_current_week(m, 2, date(2026, 10, 23))
    d = ms.describe(m, date(2026, 10, 23))
    assert d["current"] == {"number": 2, "name": "B", "starts": "2026-10-19"}
    assert d["next"]["number"] == 3 and d["next"]["starts"] == "2026-10-26"
    assert d["weekday"] == 4
    try:
        ms.set_current_week(m, 4, date(2026, 10, 23))
        raise AssertionError("should fail")
    except ValueError:
        pass


def test_menu_validation(admin):
    ok = {"meals": ["dinner", "breakfast", "breakfast"], "weeks": [week("S1", lunch="Lentejas")], "start_week": 5}
    r = admin.put("/api/v1/admin/menu", json=ok)
    assert r.status_code == 200, r.text
    got = r.json()["menu"]
    assert got["meals"] == ["breakfast", "dinner"] and got["start_week"] == 1 and got["start_date"]
    assert got["weeks"][0]["days"][3]["lunch"] == "Lentejas"
    bad_days = {"weeks": [{"name": "x", "days": [{}] * 6}]}
    assert admin.put("/api/v1/admin/menu", json=bad_days).status_code == 422
    assert admin.put("/api/v1/admin/menu", json={"meals": ["brunch"]}).status_code == 422
    too_long = {"weeks": [{"days": [{"lunch": "x" * 301}] + [{}] * 6}]}
    assert admin.put("/api/v1/admin/menu", json=too_long).status_code == 422
    assert admin.put("/api/v1/admin/menu", json={"weeks": [week(str(i)) for i in range(13)]}).status_code == 422


def test_current_week_endpoint_and_frame_payload(paired):
    admin, dev, token = paired
    admin.put("/api/v1/admin/menu", json={"meals": ["breakfast", "lunch", "dinner"],
                                          "weeks": [week("S1", lunch="A"), week("S2", lunch="B"), week("S3", lunch="C")]})
    r = admin.post("/api/v1/admin/menu/current-week", json={"week": 2})
    assert r.status_code == 200 and r.json()["current"]["number"] == 2
    assert admin.post("/api/v1/admin/menu/current-week", json={"week": 4}).status_code == 400
    assert admin.get("/api/v1/admin/menu").json()["next"]["number"] == 3
    dash = admin.get("/api/v1/device/dashboard", headers={"Authorization": f"Bearer {token}"}).json()
    m = dash["menu"]
    assert m["configured"] and len(m["weeks"]) == 3 and m["start_week"] == 2 and m["start_date"]
    assert m["weeks"][1]["days"][0]["lunch"] == "B"


def test_menu_screen_is_part_of_the_nav_order_and_empty_menu_is_not_configured(paired):
    admin, dev, token = paired
    boot = admin.get("/api/v1/device/bootstrap", headers={"Authorization": f"Bearer {token}"}).json()["config"]
    assert boot["general"]["nav_order"][-1] == "music"
    dash = admin.get("/api/v1/device/dashboard", headers={"Authorization": f"Bearer {token}"}).json()
    assert dash["menu"]["configured"] is False
