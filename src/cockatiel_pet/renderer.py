"""Feathered companion artwork, cached sprite poses and a continuous wing rig.

All images ship with the application. Qt paints the native alpha surface locally;
there is no runtime image generation, model download, browser, or network call.
"""
from dataclasses import dataclass
from importlib.resources import files
import json
import math
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QIcon, QPixmap
from .animation import gesture_weight, smoothstep
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
    """Normalize every pose to one foot anchor, with pre-multiplied alpha."""
    CACHE_SCALE = 2

    def __init__(self):
        resources = files("cockatiel_pet").joinpath("assets")
        self.metadata = json.loads(resources.joinpath("atlas.json").read_text(encoding="utf-8"))
        raw = resources.joinpath(self.metadata["image"]).read_bytes()
        self.image = QImage.fromData(raw).convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        if self.image.isNull():
            raise RuntimeError("Bundled cockatiel artwork is missing or unreadable")
        self.frames = tuple(self._frame(frame) for frame in self.metadata["frames"])
        self.wing, self.hinge = self._wing()

    def _frame(self, frame):
        cache = QImage(SURFACE_WIDTH * self.CACHE_SCALE, SURFACE_HEIGHT * self.CACHE_SCALE,
                       QImage.Format.Format_ARGB32_Premultiplied)
        cache.fill(Qt.GlobalColor.transparent)
        x, y, w, h = frame["source"]
        ax, ay = frame["anchor"]
        scale = self.metadata["logical_scale"]
        target = QRectF(FOOT.x + (x-ax)*scale, FOOT.y + (y-ay)*scale, w*scale, h*scale)
        p = QPainter(cache)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.scale(self.CACHE_SCALE, self.CACHE_SCALE)
        p.drawImage(target, self.image, QRectF(x,y,w,h))
        p.end()
        return cache

    def _wing(self):
        data = self.metadata["wing"]
        x,y,w,h = data["source"]
        layer = QImage(w,h,QImage.Format.Format_ARGB32_Premultiplied)
        layer.fill(Qt.GlobalColor.transparent)
        clip = QPainterPath()
        for i,(px,py) in enumerate(data["outline"]):
            if i == 0: clip.moveTo(px-x,py-y)
            else: clip.lineTo(px-x,py-y)
        clip.closeSubpath()
        p=QPainter(layer)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setClipPath(clip)
        p.drawImage(-x,-y,self.image)
        p.end()
        return layer, QPointF(data["hinge"][0]-x,data["hinge"][1]-y)


class CockatielRenderer:
    def __init__(self):
        self.atlas = SpriteAtlas()
        self.resting_layer = QImage(SURFACE_WIDTH*2,SURFACE_HEIGHT*2,QImage.Format.Format_ARGB32_Premultiplied)
        self.weighted_frame = QImage(SURFACE_WIDTH*2,SURFACE_HEIGHT*2,QImage.Format.Format_ARGB32_Premultiplied)
        self.branch = QPainterPath(QPointF(42,179))
        self.branch.cubicTo(90,179,109,176,140,177)
        self.branch.cubicTo(178,176,205,178,238,180)
        self.branch.quadTo(243,182,237,184)
        self.branch.cubicTo(203,181,174,182,140,183)
        self.branch.cubicTo(100,182,75,185,43,184)
        self.branch.quadTo(37,182,42,179)
        self.branch.closeSubpath()
        self.full = QPainterPath()
        self.full.addRect(QRectF(0,0,SURFACE_WIDTH,SURFACE_HEIGHT))
        self.feet = QPainterPath()
        self.feet.addRoundedRect(QRectF(105,164,83,22),3,3)
        self.body_only = self.full.subtracted(self.feet)
        head_cut=QPainterPath()
        head_cut.addRect(QRectF(122,10,79,94))
        self.stable_body=self.full.subtracted(head_cut)

    def _branch(self,p,alpha):
        if alpha <= 0: return
        p.save()
        p.setOpacity(alpha)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#8a7051"))
        p.drawPath(self.branch)
        p.setPen(QPen(QColor("#b49a73"),1.1,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(51,180),QPointF(113,179))
        p.drawLine(QPointF(161,178),QPointF(217,181))
        p.setPen(QPen(QColor("#79664f"),2.3,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
        twig=QPainterPath(QPointF(205,180))
        twig.quadTo(219,171,230,171)
        p.drawPath(twig)
        p.restore()

    def _sprite(self,p,index,opacity=1):
        if opacity <= 0: return
        p.save()
        p.setOpacity(opacity)
        p.drawImage(QRectF(0,0,SURFACE_WIDTH,SURFACE_HEIGHT),self.atlas.frames[index])
        p.restore()

    def _wing(self,p,phase,amount,far=False):
        if amount <= 0: return
        # One stable detailed wing texture rotates around its anatomical root.
        # The head/body never jump between unrelated generated flight pictures.
        angle = 62 * math.cos(phase * math.tau)
        p.save()
        p.setOpacity(amount * (.72 if far else 1))
        p.translate(148 if far else 136,108)
        if far: p.scale(-.70,.84)
        p.rotate(angle * amount)
        span=.34*(.72+.28*amount)
        p.scale(span,span)
        p.translate(-self.atlas.hinge.x(),-self.atlas.hinge.y())
        p.drawImage(0,0,self.atlas.wing)
        p.restore()

    def _resting(self,p,pose):
        frame,weight=(0,0.0) if pose.paused else (pose.idle_frame,pose.idle_weight)
        if not pose.paused:
            if pose.reacting:
                frame,weight=2,.72*gesture_weight(min(1,pose.motion_progress))
            elif abs(pose.look)>.08 and frame not in (4,5):
                frame,weight=(3 if pose.look<0 else 2),min(.60,abs(pose.look)*.65)
        head_angle=(7 if frame==2 else -5 if frame==3 else 0)*weight
        full_pose=frame in (4,5)
        if full_pose:
            # Large anatomical changes use a brief transition, not a prolonged
            # double exposure of two different head positions.
            weight=smoothstep(weight/.12)
        self.resting_layer.fill(Qt.GlobalColor.transparent)
        layer=QPainter(self.resting_layer)
        layer.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        layer.scale(2,2)
        if full_pose and weight:
            weight=max(0,min(1,weight))
            layer.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
            self._add_weighted(layer,0,255-round(weight*255))
            self._add_weighted(layer,frame,round(weight*255))
            layer.setClipping(False)
        else:
            self._sprite(layer,0)
        if not pose.paused and pose.blink>0 and frame not in (4,5):
            # Replace the eye patch instead of painting a second face over it.
            area=QRectF(132,57,54,43)
            layer.setClipRect(area)
            layer.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            layer.fillRect(area,Qt.GlobalColor.transparent)
            layer.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
            self._add_weighted(layer,0,255-round(pose.blink*255))
            self._add_weighted(layer,1,round(pose.blink*255))
        layer.end()
        if full_pose:
            p.drawImage(QRectF(0,0,SURFACE_WIDTH,SURFACE_HEIGHT),self.resting_layer)
        else:
            # Head tracking uses one stable face on a neck pivot. A neutral head
            # is removed from the body first, eliminating duplicate eyes/beaks.
            p.save();p.setClipPath(self.stable_body);self._sprite(p,0);p.restore()
            p.save()
            p.translate(149,107);p.rotate(head_angle);p.translate(-149,-107)
            p.setClipRect(QRectF(121,10,82,105))
            p.drawImage(QRectF(0,0,SURFACE_WIDTH,SURFACE_HEIGHT),self.resting_layer)
            p.restore()

    def _add_weighted(self,p,index,alpha):
        if alpha <= 0: return
        # Qt's Plus composition with global painter opacity can attenuate the
        # accumulated destination alpha. Weight each premultiplied source first,
        # then add at full opacity so feathers and faces never become bleached.
        painter=QPainter(self.weighted_frame)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.drawImage(0,0,self.atlas.frames[index])
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        painter.fillRect(self.weighted_frame.rect(),QColor(255,255,255,alpha))
        painter.end()
        p.drawImage(QRectF(0,0,SURFACE_WIDTH,SURFACE_HEIGHT),self.weighted_frame)

    def paint(self,p:QPainter,pose:Pose):
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self._branch(p,pose.branch_alpha)
        p.save()
        p.translate(FOOT.x,FOOT.y-pose.lift)
        p.rotate(pose.pitch)
        p.scale(pose.facing,1)
        # Subpixel breathing about the planted feet, without bobbing the branch.
        breath=0 if pose.paused else .0025*math.sin(pose.time*2.0)
        p.scale(1-breath*.3,1+breath)
        p.translate(-FOOT.x,-FOOT.y)
        airborne=0.0
        if not pose.paused:
            if pose.motion == "takeoff": airborne=smoothstep(pose.motion_progress)
            elif pose.motion == "landing": airborne=1-smoothstep(pose.motion_progress)
            elif pose.motion == "flying" or (pose.wing>0 and pose.branch_alpha==0): airborne=1
        phase=pose.flap_phase
        self._wing(p,phase+.04,airborne,far=True)
        if airborne:
            p.save(); p.setClipPath(self.body_only); self._sprite(p,0); p.restore()
            p.save(); p.setClipPath(self.feet); self._sprite(p,0,1-airborne); p.restore()
        else:
            self._resting(p,pose)
        self._wing(p,phase,airborne)
        p.restore()
        if pose.chirp:
            p.save()
            p.setPen(QPen(QColor("#c6a04d"),1.3,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
            p.translate(140,177-pose.lift); p.scale(pose.facing,1); p.translate(-140,-177)
            p.drawArc(QRectF(186,73,11,17),-70*16,140*16)
            p.drawArc(QRectF(190,69,15,25),-60*16,120*16)
            p.restore()

    def image(self,pose:Pose,scale=1.0):
        image=QImage(round(SURFACE_WIDTH*scale),round(SURFACE_HEIGHT*scale),QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        p=QPainter(image)
        try:
            p.scale(scale,scale)
            self.paint(p,pose)
        finally: p.end()
        return image

    def icon(self):
        return QIcon(QPixmap.fromImage(self.image(Pose(paused=True),2).copy(200,40,210,300)))
