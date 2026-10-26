"""Quiet, seeded companion gestures; independent of flight planning and Qt."""
from dataclasses import dataclass
import math
import random


def smoothstep(value):
    t = max(0.0, min(1.0, value))
    return t * t * (3 - 2 * t)


def gesture_weight(progress):
    """Ease in, hold a readable pose, then return gently to neutral."""
    return smoothstep(progress / .24) * smoothstep((1 - progress) / .30)


def flight_frame(phase):
    """Six complete anatomical cels; wrap continuously at the cycle boundary."""
    return int((phase % 1) * 6) % 6


@dataclass(frozen=True)
class BodyMotion:
    breath: float
    sway: float
    tilt: float
    crest: float
    fluff: float
    tail: float


def idle_motion(time, frame=0, weight=0, look=0, reacting=False, progress=0):
    """Independent, slow rhythms anchored above the fixed ankle/branch band.

    Gesture ids: 2/3 neck inclination, 4 small head dip/feather fluff,
    5 tail settling. No held image replaces the whole bird during idle.
    """
    weight = max(0,min(1,weight))
    turn = (1 if frame == 2 else -1 if frame == 3 else 0)*weight
    response = gesture_weight(progress) if reacting else 0
    return BodyMotion(
        .85*math.sin(time*2.35)+(.8*weight if frame == 4 else 0),
        .95*math.sin(time*.93)+.35*math.sin(time*1.71),
        2.4*turn+1.4*look+1.3*response,
        .75*math.sin(time*2.0+.7)+.3*math.sin(time*3.3),
        .007*math.sin(time*2.35)+(.022*weight if frame == 4 else 0),
        1.1*math.sin(time*.93-.65)+(2.3*weight if frame == 5 else 0))


@dataclass(frozen=True)
class IdleSample:
    frame: int = 0
    weight: float = 0.0
    blink: float = 0.0


class IdleDirector:
    """Short blinks and neck/feather/tail gestures separated by quiet gaps."""
    def __init__(self, seed=None):
        self.rng = random.Random(None if seed is None else seed ^ 0xC0CA71E1)
        self.time = 0.0
        self.frame = 0
        self.started = self.ends = 0.0
        self.blink_started = -100.0
        self.next_blink = self.rng.uniform(2.6, 5.4)
        self.next_gesture = self.rng.uniform(5, 9)

    def update(self, dt, resting=True):
        self.time += max(0, dt)
        if not resting:
            self.frame = 0
            self.next_gesture = self.time + 5
            self.next_blink = max(self.next_blink, self.time + 1)
            return
        if self.time >= self.next_blink:
            self.blink_started = self.time
            self.next_blink = self.time + self.rng.uniform(3.2, 6.5)
        if self.frame and self.time >= self.ends:
            self.frame = 0
            self.next_gesture = self.time + self.rng.uniform(7, 14)
        if not self.frame and self.time >= self.next_gesture:
            self.frame = self.rng.choices((2, 3, 4, 5), weights=(4, 3, 3, 1))[0]
            self.started = self.time
            self.ends = self.time + (2.7 if self.frame == 4 else 1.9 if self.frame == 5 else 1.6)

    def sample(self):
        elapsed = self.time - self.blink_started
        blink = math.sin(math.pi * elapsed / .16) ** 2 if 0 <= elapsed <= .16 else 0
        progress = (self.time - self.started) / max(.01, self.ends - self.started)
        return IdleSample(self.frame, gesture_weight(progress) if self.frame else 0.0, blink)
