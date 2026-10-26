import pytest
from cockatiel_pet.animation import IdleDirector, flap_weights, gesture_weight


def test_wing_cycle_is_normalized_and_continuous():
    assert flap_weights(0) == (1, 0, 0)
    assert flap_weights(.25) == (0, 1, 0)
    assert flap_weights(.5) == (0, 0, 1)
    assert flap_weights(1) == flap_weights(0)
    for i in range(1000):
        weights = flap_weights(i / 1000)
        assert sum(weights) == pytest.approx(1)
        assert all(0 <= w <= 1 for w in weights)
        next_weights = flap_weights((i + .01) / 1000)
        assert max(abs(a-b) for a,b in zip(weights,next_weights)) < .001


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


def test_flight_cancels_grooming_without_changing_flight_rng():
    a = IdleDirector(2)
    for _ in range(250): a.update(.05)
    a.update(.05, resting=False)
    assert a.sample().frame == 0
    for _ in range(20): a.update(.05)
    assert a.sample().frame == 0
