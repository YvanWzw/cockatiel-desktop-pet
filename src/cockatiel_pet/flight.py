"""Seeded primary-display flight planning; no dependencies on Qt/Win32."""
from dataclasses import dataclass
import random
from .models import Point, Rect, perch_bounds


def ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def cubic_bezier(p0, p1, p2, p3, t):
    t = min(1.0, max(0.0, t))
    u = 1 - t
    return p0 * (u ** 3) + p1 * (3 * u * u * t) + p2 * (3 * u * t * t) + p3 * (t ** 3)


@dataclass(frozen=True)
class FlightPath:
    start: Point
    c1: Point
    c2: Point
    end: Point
    duration: float

    def sample(self, progress):
        return cubic_bezier(self.start, self.c1, self.c2, self.end, ease(progress))


class FlightPlanner:
    def __init__(self, work: Rect, scale=1.0, rng=None):
        self.rng = rng or random.Random()
        self.resize(work, scale)

    def resize(self, work, scale):
        self.scale = scale
        self.bounds = perch_bounds(work, scale)
        b = self.bounds
        self.ground = Rect(b.left, min(b.bottom, b.top + 12 * scale), b.right, b.bottom)

    def initial_perch(self):
        b = self.ground
        return b.clamp(Point(b.left + b.width * .72, b.top + b.height * .68))

    def destination(self, current):
        b, s = self.ground, self.scale
        # Prefer the right-hand area without inspecting or moving desktop icons.
        left = min(b.right, b.left + min(170 * s, b.width * .16))
        candidates = [Point(self.rng.uniform(left, b.right), self.rng.uniform(b.top, b.bottom)) for _ in range(48)]
        usable = [p for p in candidates if min(200 * s, b.width * .25) <= p.distance(current) <= 1350 * s]
        if usable:
            return self.rng.choice(usable)
        target = max(candidates, key=current.distance)
        delta = target - current
        length = current.distance(target)
        return b.clamp(current + delta * min(1, 1350 * s / max(length, 1)))

    def plan(self, start, end):
        s, b = self.scale, self.bounds
        delta = end - start
        rise = min(150 * s, max(30 * s, abs(delta.x) * .18))
        c1 = b.clamp(start + Point(delta.x * .25, -rise))
        c2 = b.clamp(end - Point(delta.x * .25, rise))
        samples = [cubic_bezier(start, c1, c2, end, i / 64) for i in range(65)]
        length = sum(a.distance(z) for a, z in zip(samples, samples[1:]))
        duration = max(2.0, min(8.0, length / (self.rng.uniform(170, 240) * s)))
        return FlightPath(start, c1, c2, end, duration)
