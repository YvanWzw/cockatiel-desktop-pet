"""Original vector artwork. No downloaded assets or runtime file dependencies."""
from dataclasses import dataclass
import math
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QLinearGradient, QIcon, QPixmap
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


def path(start, *commands):
    p = QPainterPath(QPointF(*start))
    for command in commands:
        op, *values = command
        if op == "C": p.cubicTo(*values)
        elif op == "Q": p.quadTo(*values)
        elif op == "L": p.lineTo(*values)
        elif op == "Z": p.closeSubpath()
    return p


class CockatielRenderer:
    def __init__(self):
        self.outline = QColor("#4e555d")
        self.tail = path((119, 133), ("C", 112, 155, 100, 184, 83, 202), ("Q", 105, 193, 130, 155), ("Z",))
        self.tail_light = path((127, 142), ("Q", 117, 176, 96, 198), ("Q", 119, 186, 140, 150), ("Z",))
        self.body = path((136, 96), ("C", 111, 100, 112, 133, 119, 152), ("C", 128, 173, 152, 169, 160, 151),
                         ("C", 172, 131, 169, 106, 153, 99), ("Z",))
        self.wing_folded = path((126, 105), ("C", 109, 113, 119, 146, 133, 157), ("C", 150, 158, 152, 126, 137, 109), ("Z",))
        self.crest = path((144, 65), ("Q", 138, 51, 137, 44), ("Q", 148, 51, 152, 59), ("Q", 153, 45, 157, 41),
                          ("Q", 163, 50, 163, 60), ("Q", 169, 51, 174, 50), ("Q", 174, 62, 169, 70), ("Z",))
        self.branch = path((39, 182), ("Q", 88, 179, 140, 177), ("Q", 192, 175, 240, 180),
                           ("Q", 249, 181, 241, 188), ("Q", 190, 183, 141, 187), ("Q", 81, 189, 40, 190), ("Q", 34, 187, 39, 182), ("Z",))
        self.twigs = path((92, 185), ("Q", 78, 200, 66, 201))
        self.twig2 = path((207, 181), ("Q", 221, 167, 233, 168))
        self.body_gradient = QLinearGradient(119, 112, 160, 159)
        self.body_gradient.setColorAt(0, QColor("#d3d6d5"))
        self.body_gradient.setColorAt(1, QColor("#9fa7ab"))
        self.head_gradient = QLinearGradient(142, 63, 167, 104)
        self.head_gradient.setColorAt(0, QColor("#fff2a3"))
        self.head_gradient.setColorAt(1, QColor("#ead267"))

    def _shape(self, p, shape, fill, width=1.5, outline=None):
        p.setPen(QPen(outline or self.outline, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(QColor(fill) if isinstance(fill, str) else fill)
        p.drawPath(shape)

    def paint(self, p: QPainter, pose: Pose):
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # The branch stays anchored to the ground while the body lifts away.
        if pose.branch_alpha > 0:
            p.save()
            p.setOpacity(pose.branch_alpha)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor("#7a553d"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawPath(self.twigs)
            p.drawPath(self.twig2)
            self._shape(p, self.branch, "#a87850", 1.4, QColor("#74523c"))
            p.setPen(QPen(QColor("#c6986b"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawPath(path((48, 184), ("Q", 103, 182, 133, 181)))
            p.drawPath(path((171, 180), ("Q", 203, 178, 224, 183)))
            p.setPen(QPen(QColor("#80563d"), 1.2))
            p.drawArc(QRectF(190, 180, 12, 5), 0, 360 * 16)
            p.restore()
        p.save()
        p.translate(FOOT.x, FOOT.y - pose.lift)
        p.rotate(pose.pitch)
        p.scale(pose.facing, 1)
        p.translate(-FOOT.x, -FOOT.y)
        breath = 0 if pose.paused else math.sin(pose.time * 2.1) * 0.8
        p.translate(0, breath)
        self._shape(p, self.tail, "#89959e")
        self._shape(p, self.tail_light, "#bec5c6", 1)
        # A second, distant wing makes the flap silhouette readable.
        if pose.wing > 0.08:
            p.save()
            p.translate(149, 113)
            p.rotate(25 - 90 * pose.wing)
            self._shape(p, path((0, 0), ("C", 9, -15, 47, -24, 65, -13), ("Q", 54, 7, 8, 15), ("Z",)), "#acb6bc")
            p.restore()
        self._shape(p, self.body, self.body_gradient)
        # Soft breast highlight.
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#e3e4dc"))
        p.drawEllipse(QRectF(143, 113, 17, 35))
        p.save()
        p.translate(154, 88)
        tilt = pose.look * 8 + (math.sin(pose.time * 9) * 7 if pose.reacting else 0)
        groom = math.sin(pose.time * 2) * 7 if not pose.paused and 15 < pose.time % 29 < 17 else 0
        p.rotate(tilt + groom)
        p.translate(-154, -88)
        self._shape(p, self.crest, "#f1d86b", 1.1, QColor("#a6954e"))
        p.setBrush(self.head_gradient)
        p.setPen(QPen(QColor("#8e854f"), 1.3))
        p.drawEllipse(QRectF(132, 60, 46, 48))
        # Curved charcoal beak, warm cere and orange cheek patch.
        self._shape(p, path((174, 80), ("Q", 191, 83, 178, 95), ("Q", 179, 88, 172, 88), ("Z",)), "#737675", 1)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#e58b35"))
        p.drawEllipse(QRectF(157, 87, 16, 16))
        p.setBrush(QColor("#f8a14b"))
        p.drawEllipse(QRectF(159, 88, 11, 10))
        blinking = (pose.time % 4.9 > 4.72 or pose.reacting) and not pose.paused
        p.setPen(QPen(QColor("#2f363c"), 2.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        if blinking:
            p.drawPath(path((161, 80), ("Q", 165, 83, 169, 80)))
        else:
            p.setBrush(QColor("#28323a"))
            p.drawEllipse(QRectF(162, 76, 7, 8))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor("#fffdf0"))
            p.drawEllipse(QRectF(164, 77, 2, 2.5))
        p.restore()
        # Front wing rotates around the shoulder; feather stripes follow it.
        p.save()
        p.translate(129, 111)
        p.rotate(-115 * pose.wing)
        p.translate(-129, -111)
        self._shape(p, self.wing_folded, "#87939d")
        p.setPen(QPen(QColor("#f0f0df"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawPath(path((128, 119), ("Q", 132, 133, 141, 139)))
        p.setPen(QPen(QColor("#65747f"), 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for x in (125, 130, 135):
            p.drawPath(path((x, 139), ("Q", x + 3, 148, x + 7, 151)))
        p.restore()
        p.translate(0, -breath)  # Feet stay planted while the body breathes.
        p.setPen(QPen(QColor("#8c7770"), 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for x in (132, 148):
            p.drawLine(QPointF(x, 163), QPointF(x - 1, 175))
            for dx in (-5, 0, 5):
                p.drawPath(path((x - 1, 174), ("Q", x + dx, 174, x + dx, 178)))
        p.restore()
        if pose.chirp:
            p.setPen(QPen(QColor("#e1ba51"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for x, y, a in ((201, 73, -1), (207, 86, 0), (199, 99, 1)):
                p.drawLine(QPointF(x, y), QPointF(x + 7, y + a * 3))

    def image(self, pose: Pose, scale=1.0):
        image = QImage(round(SURFACE_WIDTH * scale), round(SURFACE_HEIGHT * scale), QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        p = QPainter(image)
        try:
            p.scale(scale, scale)
            self.paint(p, pose)
        finally:
            p.end()
        return image

    def icon(self):
        return QIcon(QPixmap.fromImage(self.image(Pose()).copy(80, 40, 110, 150)))
