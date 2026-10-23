from cockatiel_pet.models import Rect
from cockatiel_pet.state_machine import PetController, State

WORK = Rect(0, 0, 1920, 1040)


def advance(c, seconds, dt=1/60):
    while seconds > 1e-9:
        step = min(dt, seconds)
        c.update(step)
        seconds -= step


def test_long_initial_idle_then_full_cycle():
    c = PetController(WORK, seed=1)
    assert c.branch_alpha == 1 and c.state == State.PERCHED
    advance(c, 19)
    assert c.state == State.PERCHED
    advance(c, c.idle_duration - 19 + .2)
    assert c.state == State.TAKEOFF
    advance(c, .5)
    assert c.state == State.FLYING and c.branch_alpha == 0
    advance(c, c.path.duration + .8)
    assert c.state == State.PERCHED and c.branch_alpha == 1


def test_pause_midflight_settles_in_place_and_resume_waits():
    c = PetController(WORK, seed=9)
    c.fly_now()
    advance(c, 1.5)
    position = c.position
    c.set_paused(True)
    assert c.position.distance(position) < 1
    advance(c, 30)
    assert c.position == position and c.state == State.PAUSED and c.branch_alpha == 1
    assert not c.fly_now()
    c.set_paused(False)
    advance(c, 10)
    assert c.state == State.PERCHED


def test_elapsed_time_independent_and_seed_reproducible():
    a, b = (PetController(WORK, seed=52) for _ in range(2))
    a.fly_now(); b.fly_now()
    advance(a, 3.1, 1 / 30)
    advance(b, 3.1, 1 / 120)
    assert a.state == b.state
    assert a.position.distance(b.position) < 1e-7
    assert abs(a.age - b.age) < 1e-7


def test_reaction_cooldown_preserves_idle_deadline_and_sleep_clamp():
    c = PetController(WORK, seed=8)
    original = c.idle_duration
    assert c.react("hover")
    advance(c, 1)
    assert not c.react("hover")
    advance(c, 2.1)
    assert c.react("hover") and c.idle_duration == original
    before = c.time
    c.update(100)
    assert abs(c.time - before - .05) < 1e-8


def test_visual_continuity_at_takeoff_and_landing():
    c = PetController(WORK, seed=31)
    c.fly_now()
    advance(c, c.TAKEOFF_SECONDS - .0001)
    before = c.position.y - c.lift
    c.update(.0002)
    assert abs((c.position.y - c.lift) - before) < .01
    advance(c, c.path.duration - c.age - .0001)
    before = c.position.y - c.lift
    c.update(.0002)
    assert abs((c.position.y - c.lift) - before) < .01
