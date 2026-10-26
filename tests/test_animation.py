import pytest
from cockatiel_pet.animation import IdleDirector, flight_frame, gesture_weight, idle_motion


def test_whole_bird_flight_cels_advance_in_order_and_wrap():
    assert [flight_frame((i+.5)/6) for i in range(6)] == list(range(6))
    assert flight_frame(0)==flight_frame(1)==flight_frame(2)==0
    assert flight_frame(1-1e-8)==5
    assert flight_frame(-.01)==5


def test_background_breathing_and_sway_are_continuous_even_without_gestures():
    a,b=idle_motion(1),idle_motion(1.001)
    for field in ("breath","sway","tilt","crest","fluff","tail"):
        assert abs(getattr(a,field)-getattr(b,field))<.01
    assert idle_motion(0)!=idle_motion(2)
    for t in range(60):
        motion=idle_motion(t)
        assert abs(motion.breath)<1 and abs(motion.sway)<1.4 and abs(motion.tail)<1.2


def test_gestures_start_and_end_neutral():
    assert gesture_weight(0) == gesture_weight(1) == 0
    assert gesture_weight(.5) == 1
    assert gesture_weight(.001) < .001
    assert gesture_weight(.999) < .001


def test_seeded_gestures_and_short_blinks_with_quiet_gaps():
    a, b = IdleDirector(21), IdleDirector(21)
    seen, blinking_frames, quiet_frames = set(), 0, 0
    for _ in range(1200):
        a.update(.05); b.update(.05)
        assert a.sample() == b.sample()
        sample = a.sample()
        seen.add(sample.frame)
        blinking_frames += sample.blink > .1
        quiet_frames += sample.frame == 0
    assert seen & {2,3,4,5}
    assert quiet_frames > 850
    assert 0 < blinking_frames < 70


def test_flight_cancels_idle_gestures_without_changing_flight_rng():
    a = IdleDirector(2)
    for _ in range(250): a.update(.05)
    a.update(.05, resting=False)
    assert a.sample().frame == 0
    for _ in range(20): a.update(.05)
    assert a.sample().frame == 0
