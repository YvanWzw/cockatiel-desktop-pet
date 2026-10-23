import pytest
from cockatiel_pet.models import Point, FOOT
from cockatiel_pet.mouse_observer import MouseObserver, PointerSample, bird_hit

HEAD = Point(163, 81)


def sample(observer, time, p=HEAD, down=False, desktop=True, enabled=True):
    return observer.observe(PointerSample(p, down, desktop), time, FOOT, 1, enabled=enabled)


def test_hover_dwell_and_cooldown():
    o = MouseObserver()
    assert sample(o, 0).reaction is None
    assert sample(o, .29).reaction is None
    assert sample(o, .31).reaction == "hover"
    assert sample(o, 2).reaction is None
    assert sample(o, 3.32).reaction == "hover"


def test_click_is_rising_edge_only_and_rate_limited():
    o = MouseObserver()
    sample(o, 0)
    assert sample(o, .1, down=True).reaction == "click"
    assert sample(o, .2, down=True).reaction is None
    sample(o, .21, down=False)
    assert sample(o, .22, down=True).reaction is None
    sample(o, 2.2, down=False)
    assert sample(o, 2.3, down=True).reaction == "click"


def test_apps_taskbar_unknown_disabled_and_held_button_entry():
    for enabled, exposed in ((True, False), (False, True), (False, False)):
        o = MouseObserver()
        sample(o, 0, desktop=exposed, enabled=enabled)
        assert sample(o, 1, down=True, desktop=exposed, enabled=enabled).reaction is None
        # Holding a click from an application must never become a desktop click.
        assert sample(o, 1.01, down=True).reaction != "click"
    assert sample(MouseObserver(), 0, down=True).reaction is None


def test_branch_and_transparent_corners_are_not_hit_targets():
    for p in (Point(0,0),Point(45,185),Point(220,181),Point(140,181)):
        assert not bird_hit(p)


def test_dpi_and_facing_transform():
    o = MouseObserver()
    anchor = Point(800, 900)
    physical_head = anchor + Point(140 - HEAD.x, HEAD.y - FOOT.y) * 1.5
    s = PointerSample(physical_head, False, True)
    assert o.observe(s, 0, anchor, 1.5, -1).reaction is None
    assert o.observe(s, .4, anchor, 1.5, -1).reaction == "hover"


def test_exposure_loss_resets_hover_and_missing_sample_is_ignored():
    o = MouseObserver()
    sample(o, 0)
    sample(o, .2, desktop=False)
    assert sample(o, .4).reaction is None
    assert o.observe(None, .5, FOOT, 1).reaction is None
