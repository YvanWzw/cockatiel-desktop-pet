"""Offline cockatiel sprites with planted-foot deformation and whole-bird flight.

Flight cels contain the complete anatomy: no wing cutout is attached to a standing
body. The perched branch and gripping toes share one source image and transform.
"""
from dataclasses import dataclass
from importlib.resources import files
import json
import math
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QIcon, QPixmap
from .animation import flight_frame, idle_motion, smoothstep
from .models import FOOT, SURFACE_WIDTH, SURFACE_HEIGHT


@dataclass
class Pose:
    time: float = 0
    facing: int = 1
    wing: float = 0
    lift: float = 0
    pitch: float = 0
    branch_alpha: float = 1
    look: float = 0
    reacting: bool = False
    chirp: bool = False
    paused: bool = False
    motion: str = "perched"
    motion_progress: float = 0
    flap_phase: float = 0
    idle_frame: int = 0
    idle_weight: float = 0
    blink: float = 0


class SpriteAtlas:
    """Cache premultiplied artwork in a shared logical coordinate system."""
    CACHE_SCALE = 2

    def __init__(self):
        resources = files("cockatiel_pet").joinpath("assets")
        self.metadata = json.loads(resources.joinpath("atlas.json").read_text(encoding="utf-8"))
        self.images = {}
        for kind in ("perch", "flight"):
            data = resources.joinpath(self.metadata[kind]["image"]).read_bytes()
            image = QImage.fromData(data).convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
            if image.isNull():
                raise RuntimeError(f"Bundled {kind} artwork is missing or unreadable")
            self.images[kind] = image
        self.frames = self._frames("perch")
        self.flight = self._frames("flight")

    def _frames(self, kind):
        group = self.metadata[kind]
        result = []
        for frame in group["frames"]:
            image = QImage(SURFACE_WIDTH*2, SURFACE_HEIGHT*2, QImage.Format.Format_ARGB32_Premultiplied)
            image.fill(Qt.GlobalColor.transparent)
            x,y,w,h = frame["source"]
            ax,ay = frame["anchor"]
            tx,ty = group["target"]
            scale = group["scale"]
            target = QRectF(tx+(x-ax)*scale, ty+(y-ay)*scale, w*scale, h*scale)
            p = QPainter(image)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            p.scale(2,2)
            p.drawImage(target, self.images[kind], QRectF(x,y,w,h))
            p.end()
            result.append(image)
        return tuple(result)


class CockatielRenderer:
    PLANTED_TOP = 164
    PLANTED_BOTTOM = 188

    def __init__(self):
        self.atlas = SpriteAtlas()
        self.resting_layer = self.atlas.frames[0].copy()
        self.eye_clip = QPainterPath()
        # Closed-eye source is registered to the open eyes, not to its branch.
        self.eye_clip.addEllipse(QRectF(122.8,73.5,8.5,8))
        self.eye_clip.addEllipse(QRectF(150.2,73.5,8.5,8))

    @staticmethod
    def _draw(p, image):
        p.drawImage(QRectF(0,0,SURFACE_WIDTH,SURFACE_HEIGHT), image)

    def _resting(self, p, pose):
        self.resting_layer = self.atlas.frames[0].copy()
        if not pose.paused and pose.blink > 0:
            layer = QPainter(self.resting_layer)
            layer.scale(2,2)
            layer.setClipPath(self.eye_clip)
            layer.setOpacity(max(0,min(1,pose.blink)))
            self._draw(layer,self.atlas.frames[1])
            layer.end()
        if pose.paused:
            self._draw(p,self.resting_layer)
            return
        motion = idle_motion(pose.time,pose.idle_frame,pose.idle_weight,pose.look,
                             pose.reacting,pose.motion_progress)
        # A continuous row deformation bends the neck/crest without cutting out
        # a rectangular head. Every row below the ankle stays exactly planted.
        def upper(y):
            planted = smoothstep((self.PLANTED_TOP-y)/90)
            head = smoothstep((115-y)/40)
            crest = smoothstep((65-y)/45)
            dx = motion.sway*planted + motion.tilt*(105-y)*.055*head + motion.crest*crest
            chest = math.exp(-((y-128)/26)**2)
            width = 1 + motion.fluff*chest
            dy = -motion.breath*planted
            return dx,y+dy,width
        p.save()
        p.setClipRect(QRectF(0,0,280,self.PLANTED_TOP))
        for y in range(0,self.PLANTED_TOP,2):
            dx,ty,width = upper(y)
            _,bottom,_ = upper(y+2)
            # Sample the full texture under the strip clip. Cropping tiny
            # source strips first clamps bilinear filtering at each strip edge
            # and produces visible horizontal bands on pale feathers.
            stretch=(bottom-ty)/2
            p.save()
            p.setClipRect(QRectF(0,ty,280,bottom-ty),Qt.ClipOperation.IntersectClip)
            p.translate(140-140*width+dx,ty-y*stretch)
            p.scale(width,stretch)
            self._draw(p,self.resting_layer)
            p.restore()
        p.restore()
        p.drawImage(QRectF(0,self.PLANTED_TOP,280,self.PLANTED_BOTTOM-self.PLANTED_TOP),
                    self.resting_layer,QRectF(0,self.PLANTED_TOP*2,560,(self.PLANTED_BOTTOM-self.PLANTED_TOP)*2))
        # Tail is below the branch; its movement eases out of the fixed contact
        # band rather than moving the toes or warping the bark.
        for y in range(self.PLANTED_BOTTOM,240,2):
            dx = motion.tail*smoothstep((y-self.PLANTED_BOTTOM)/28)
            p.save()
            p.setClipRect(QRectF(0,y,280,2))
            p.translate(dx,0)
            self._draw(p,self.resting_layer)
            p.restore()

    @staticmethod
    def airborne(pose):
        if pose.paused:
            return False
        if pose.motion == "takeoff":
            return pose.motion_progress >= .24
        if pose.motion == "landing":
            return pose.motion_progress < .76
        return pose.motion == "flying" or (pose.wing > 0 and pose.branch_alpha == 0)

    def paint(self,p:QPainter,pose:Pose):
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        flying = self.airborne(pose)
        p.save()
        p.translate(FOOT.x,FOOT.y)
        if flying:
            p.translate(0,-pose.lift)
            p.rotate(pose.pitch)
        p.scale(pose.facing,1)
        p.translate(-FOOT.x,-FOOT.y)
        if flying:
            # Cel animation avoids translucent double wings and preserves the
            # entire rendered shoulder/torso/feet connection on every frame.
            self._draw(p,self.atlas.flight[flight_frame(pose.flap_phase)])
        else:
            self._resting(p,pose)
        p.restore()
        if pose.chirp and not flying:
            p.save()
            p.translate(FOOT.x,FOOT.y)
            p.scale(pose.facing,1)
            p.translate(-FOOT.x,-FOOT.y)
            p.setPen(QPen(QColor("#c6a04d"),1.2,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
            p.drawArc(QRectF(166,74,10,16),-70*16,140*16)
            p.drawArc(QRectF(170,70,14,24),-60*16,120*16)
            p.restore()

    def image(self,pose:Pose,scale=1.0):
        image=QImage(round(SURFACE_WIDTH*scale),round(SURFACE_HEIGHT*scale),QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        p=QPainter(image)
        try:
            p.scale(scale,scale)
            self.paint(p,pose)
        finally:
            p.end()
        return image

    def icon(self):
        return QIcon(QPixmap.fromImage(self.image(Pose(paused=True),2).copy(205,50,150,270)))
