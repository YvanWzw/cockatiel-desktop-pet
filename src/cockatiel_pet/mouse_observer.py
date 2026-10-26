"""Passive samples only. No pointer history beyond the previous sample."""
from dataclasses import dataclass
import math
from .models import Point, to_local


@dataclass(frozen=True)
class PointerSample:
    position: Point
    down: bool
    desktop_exposed: bool


@dataclass(frozen=True)
class Interaction:
    look: float = 0
    reaction: str | None = None


def bird_hit(local: Point):
    """Head/body ellipses exclude transparent margins and the entire branch."""
    return ((local.x - 140) / 24) ** 2 + ((local.y - 84) / 25) ** 2 <= 1 or ((local.x - 140) / 37) ** 2 + ((local.y - 132) / 35) ** 2 <= 1


class MouseObserver:
    def __init__(self):
        self.previous = None
        self.hover_since = None
        self.last_hover = self.last_click = -math.inf

    def observe(self, sample: PointerSample | None, now, anchor, scale, facing=1, enabled=True):
        if sample is None:
            self.previous = None
            self.hover_since = None
            return Interaction()
        rising = bool(self.previous is not None and sample.down and not self.previous.down)
        self.previous = sample  # Also update while disabled/covered to avoid false clicks.
        if not enabled or not sample.desktop_exposed:
            self.hover_since = None
            return Interaction()
        local = to_local(sample.position, anchor, scale)
        if facing < 0:
            local = Point(280 - local.x, local.y)
        head = Point(140, 84)
        look = max(-1, min(1, (local.x - head.x) / 80)) * facing if local.distance(head) < 160 else 0
        if not bird_hit(local):
            self.hover_since = None
            return Interaction(look)
        if self.hover_since is None:
            self.hover_since = now
        if rising and now - self.last_click >= 2:
            self.last_click = now
            return Interaction(look, "click")
        if now - self.hover_since >= .3 and now - self.last_hover >= 3:
            self.last_hover = now
            return Interaction(look, "hover")
        return Interaction(look)
