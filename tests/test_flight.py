import random
import pytest
from cockatiel_pet.flight import FlightPlanner, cubic_bezier, ease
from cockatiel_pet.models import Point, Rect


def test_bezier_endpoints_and_easing():
    points = (Point(0, 10), Point(20, -5), Point(90, -5), Point(110, 20))
    assert cubic_bezier(*points, 0) == points[0]
    assert cubic_bezier(*points, 1) == points[-1]
    assert ease(0) == 0 and ease(1) == 1
    assert ease(.0001) < .000001 and ease(.9999) > .999999


@pytest.mark.parametrize("work,scale", [(Rect(0, 0, 1920, 1040), 1), (Rect(-1920, -500, 0, 540), 1), (Rect(0, 0, 3840, 2088), 1.5)])
def test_seeded_destinations_and_continuous_bounded_paths(work, scale):
    planner = FlightPlanner(work, scale, random.Random(42))
    position = planner.initial_perch()
    for _ in range(100):
        destination = planner.destination(position)
        assert planner.ground.contains(destination)
        p = planner.plan(position - Point(0, 12 * scale), destination - Point(0, 12 * scale))
        assert p.sample(0) == p.start and p.sample(1) == p.end
        samples = [p.sample(i / 200) for i in range(201)]
        assert all(planner.bounds.contains(s) for s in samples)
        assert max(a.distance(b) for a, b in zip(samples, samples[1:])) < 25 * scale
        assert 2 <= p.duration <= 8
        position = destination
