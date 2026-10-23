"""Geometry is in physical desktop pixels; artwork is in logical design units."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, scale):
        return Point(self.x * scale, self.y * scale)

    def distance(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)


@dataclass(frozen=True)
class Rect:
    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.bottom - self.top

    def contains(self, p: Point):
        return self.left <= p.x <= self.right and self.top <= p.y <= self.bottom

    def covers(self, other: "Rect"):
        return self.left <= other.left and self.top <= other.top and self.right >= other.right and self.bottom >= other.bottom

    def clamp(self, p: Point):
        return Point(min(self.right, max(self.left, p.x)), min(self.bottom, max(self.top, p.y)))


SURFACE_WIDTH = 280
SURFACE_HEIGHT = 240
FOOT = Point(140, 177)
BRANCH_TOP = FOOT.y


def effective_scale(work: Rect, dpi_scale: float, pet_scale: float) -> float:
    """Shrink on tiny displays so the entire viewport, including margins, fits."""
    return max(0.1, min(dpi_scale * pet_scale, (work.width - 20) / SURFACE_WIDTH, (work.height - 20) / SURFACE_HEIGHT))


def perch_bounds(work: Rect, scale: float, padding: float = 40) -> Rect:
    pad = min(padding, max(0, (work.width - SURFACE_WIDTH * scale) / 2), max(0, (work.height - SURFACE_HEIGHT * scale) / 2))
    return Rect(work.left + FOOT.x * scale + pad, work.top + FOOT.y * scale + pad,
                work.right - (SURFACE_WIDTH - FOOT.x) * scale - pad,
                work.bottom - (SURFACE_HEIGHT - FOOT.y) * scale - pad)


def surface_origin(anchor: Point, scale: float) -> Point:
    return anchor - FOOT * scale


def to_local(screen: Point, anchor: Point, scale: float) -> Point:
    return (screen - surface_origin(anchor, scale)) * (1 / scale)
