"""Build an original application icon and artwork preview using our renderer."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
import struct
import argparse
from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage, QPainter, QColor, QFont
from PySide6.QtWidgets import QApplication
from cockatiel_pet.renderer import CockatielRenderer, Pose


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("work/build-assets"))
    parser.add_argument("--preview", type=Path, default=Path("docs/artwork-preview.png"))
    args = parser.parse_args()
    app = QApplication([])
    renderer = CockatielRenderer()
    image = renderer.image(Pose(paused=True), 3).copy(240, 110, 330, 510).scaled(256, 256, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    square = QImage(256, 256, QImage.Format.Format_ARGB32_Premultiplied)
    square.fill(Qt.GlobalColor.transparent)
    p = QPainter(square)
    p.drawImage((256-image.width())//2, (256-image.height())//2, image)
    p.end()
    data, buffer = QByteArray(), QBuffer()
    buffer.setBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not square.save(buffer, "PNG"):
        raise RuntimeError("Could not encode icon")
    png = bytes(data)
    args.output.mkdir(parents=True, exist_ok=True)
    # ICO directory with one 256x256 PNG entry (supported since Windows Vista).
    (args.output/"pet.ico").write_bytes(struct.pack("<HHH",0,1,1)+struct.pack("<BBBBHHII",0,0,0,0,1,32,len(png),22)+png)
    preview = QImage(1000, 360, QImage.Format.Format_ARGB32_Premultiplied)
    preview.fill(QColor("#f1f2ee"))
    p = QPainter(preview)
    p.setPen(QColor("#343c43"))
    p.setFont(QFont("Segoe UI", 12))
    for x, title, pose in ((20,"Resting",Pose(paused=True)), (350,"Flying",Pose(time=.1,wing=.9,branch_alpha=0,pitch=-8)), (680,"A quiet hello",Pose(time=.2,reacting=True,chirp=True))):
        p.drawText(x+90, 48, title)
        p.save()
        p.translate(x,75)
        renderer.paint(p,pose)
        p.restore()
    p.end()
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    if not preview.save(str(args.preview)):
        raise RuntimeError("Could not save preview")


if __name__ == "__main__":
    main()
