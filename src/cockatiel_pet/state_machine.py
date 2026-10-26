"""Deterministic elapsed-time controller. Large sleep gaps are discarded."""
from enum import Enum
import logging
import math
import random
from .flight import FlightPlanner, ease
from .models import Point
from .animation import IdleDirector

log = logging.getLogger(__name__)


class State(str, Enum):
    PERCHED = "perched"
    TAKEOFF = "takeoff"
    FLYING = "flying"
    LANDING = "landing"
    REACTING = "reacting"
    PAUSED = "paused"


class PetController:
    TAKEOFF_SECONDS = .48
    LANDING_SECONDS = .65
    REACTION_SECONDS = .75

    def __init__(self, work, scale=1, seed=None, idle_min=20, idle_max=55, paused=False):
        self.rng = random.Random(seed)
        self.planner = FlightPlanner(work, scale, self.rng)
        self.idle_min = max(10, idle_min)
        self.idle_max = max(self.idle_min, idle_max)
        self.position = self.planner.initial_perch()
        self.destination = self.position
        self.state = State.PAUSED if paused else State.PERCHED
        self.age = self.time = self.idle_elapsed = 0.0
        self.idle_duration = self.rng.uniform(self.idle_min, self.idle_max)
        self.path = None
        self.facing = 1
        self.look = self.look_target = 0.0
        self.reaction_kind = "hover"
        self.last_reaction = -100.0
        self.idle_animation = IdleDirector(seed)

    def _enter(self, state):
        log.debug("State %s -> %s", self.state.value, state.value)
        self.state, self.age = state, 0.0

    def _reset_idle(self):
        self.idle_elapsed = 0.0
        self.idle_duration = self.rng.uniform(self.idle_min, self.idle_max)

    def fly_now(self):
        if self.state not in (State.PERCHED, State.REACTING):
            return False
        self.destination = self.planner.destination(self.position)
        lift = Point(0, 12 * self.planner.scale)
        self.path = self.planner.plan(self.position - lift, self.destination - lift)
        self.facing = 1 if self.destination.x >= self.position.x else -1
        self._enter(State.TAKEOFF)
        return True

    def react(self, kind):
        if self.state != State.PERCHED or self.time - self.last_reaction < (2 if kind == "click" else 3):
            return False
        self.last_reaction = self.time
        self.reaction_kind = kind
        self._enter(State.REACTING)
        return True

    def set_paused(self, paused):
        if paused and self.state != State.PAUSED:
            # Settle in place: preserve the visible foot coordinate, clamp, and
            # instantly fold wings with a branch beneath both feet.
            self.position = self.planner.ground.clamp(self.position - Point(0, self.lift * self.planner.scale))
            self.path = None
            self.look = self.look_target = 0
            self._enter(State.PAUSED)
        elif not paused and self.state == State.PAUSED:
            self._reset_idle()
            self._enter(State.PERCHED)

    def resize(self, work, scale):
        paused = self.state == State.PAUSED
        self.planner.resize(work, scale)
        self.position = self.planner.ground.clamp(self.position)
        self.path = None
        self._reset_idle()
        self._enter(State.PAUSED if paused else State.PERCHED)

    @property
    def lift(self):
        if self.state == State.TAKEOFF:
            t = self.age / self.TAKEOFF_SECONDS
            if t < .25:
                return -3 * math.sin(t * 4 * math.pi / 2)
            return -3 + 15 * ease((t - .25) / .75)
        if self.state == State.LANDING:
            return 12 * (1 - ease(self.age / self.LANDING_SECONDS))
        return 0

    @property
    def branch_alpha(self):
        if self.state == State.FLYING:
            return 0
        if self.state == State.TAKEOFF:
            return 1 - ease((self.age / self.TAKEOFF_SECONDS - .15) / .65)
        if self.state == State.LANDING:
            return ease(self.age / self.LANDING_SECONDS)
        return 1

    def update(self, dt):
        if self.state == State.PAUSED or not math.isfinite(dt) or dt <= 0:
            return
        # Normal idle frames can be >50 ms. Substep them without slowing time.
        dt = .05 if dt > .5 else dt
        while dt > 1e-9:
            step = min(dt, .05)
            self._step(step)
            dt -= step

    def _step(self, dt):
        self.time += dt
        self.idle_animation.update(dt, self.state == State.PERCHED)
        self.look += (self.look_target - self.look) * (1 - math.exp(-dt * 6))
        remaining = dt
        while remaining > 1e-9:
            duration = {State.PERCHED: self.idle_duration - self.idle_elapsed + self.age,
                        State.TAKEOFF: self.TAKEOFF_SECONDS,
                        State.FLYING: self.path.duration if self.path else 0,
                        State.LANDING: self.LANDING_SECONDS,
                        State.REACTING: self.REACTION_SECONDS}.get(self.state, math.inf)
            used = min(remaining, max(0, duration - self.age))
            self.age += used
            if self.state == State.PERCHED:
                self.idle_elapsed += used
            elif self.state == State.FLYING and self.path:
                self.position = self.path.sample(self.age / self.path.duration)
            remaining -= used
            if self.age < duration - 1e-9:
                break
            if self.state == State.PERCHED:
                self.fly_now()
            elif self.state == State.TAKEOFF:
                self.position = self.path.start
                self._enter(State.FLYING)
            elif self.state == State.FLYING:
                self.position = self.destination
                self._enter(State.LANDING)
            elif self.state == State.LANDING:
                self.position = self.destination
                self._reset_idle()
                self._enter(State.PERCHED)
            elif self.state == State.REACTING:
                self._enter(State.PERCHED)  # Preserve the autonomous idle budget.

    def pose(self):
        from .renderer import Pose  # Pure state tests need no Qt imports.
        wing = 0
        pitch = 0
        if self.state == State.TAKEOFF:
            wing = ease(self.age / self.TAKEOFF_SECONDS) * .7
        elif self.state == State.FLYING:
            progress = self.age / self.path.duration
            envelope = min(ease(self.age / .2), ease((self.path.duration - self.age) / .2))
            wing = .7 - .2 * ease(progress) + .45 * envelope * math.sin(self.age * math.tau * 7.5)
            a = self.path.sample(max(0, self.age / self.path.duration - .01))
            b = self.path.sample(min(1, self.age / self.path.duration + .01))
            pitch = max(-15, min(15, math.degrees(math.atan2(b.y - a.y, max(1, abs(b.x - a.x)))) * .35)) * self.facing
        elif self.state == State.LANDING:
            wing = .5 * (1 - ease(self.age / self.LANDING_SECONDS))
        idle = self.idle_animation.sample()
        motion_duration = self.TAKEOFF_SECONDS if self.state == State.TAKEOFF else self.LANDING_SECONDS if self.state == State.LANDING else self.REACTION_SECONDS
        reaction_blink = math.sin(math.pi * self.age / .18) ** 2 if self.state == State.REACTING and self.age < .18 else 0
        return Pose(time=self.time, facing=self.facing, wing=wing, lift=self.lift, pitch=pitch,
                    branch_alpha=self.branch_alpha, look=self.look * self.facing,
                    reacting=self.state == State.REACTING,
                    chirp=self.state == State.REACTING and self.reaction_kind == "click" and self.age < .5,
                    paused=self.state == State.PAUSED, motion=self.state.value,
                    motion_progress=self.age / motion_duration,
                    flap_phase=(self.time * 4.0) % 1,
                    idle_frame=idle.frame, idle_weight=idle.weight,
                    blink=max(idle.blink, reaction_blink))
