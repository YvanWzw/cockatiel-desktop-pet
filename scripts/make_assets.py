"""Build an original application icon and artwork preview using our renderer."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
import struct
import argparse
from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage, QPainter, QColor, QFont, QFontDatabase
from PySide6.QtWidgets import QApplication
from cockatiel_pet.renderer import CockatielRenderer, Pose


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("work/build-assets"))
    parser.add_argument("--preview", type=Path, default=Path("docs/artwork-preview.png"))
    args = parser.parse_args()
    app = QApplication([])
    # The offscreen Qt platform has no Windows font database of its own.
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    for name in ("segoeui.ttf", "msyh.ttc"):
        if (fonts/name).is_file(): QFontDatabase.addApplicationFont(str(fonts/name))
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
    preview = QImage(1000, 650, QImage.Format.Format_ARGB32_Premultiplied)
    preview.fill(QColor("#f1f2ee"))
    p = QPainter(preview)
    p.setPen(QColor("#343c43"))
    p.setFont(QFont("Microsoft YaHei" if "Microsoft YaHei" in QFontDatabase.families() else "Segoe UI", 12))
    poses=((20,75,"安静陪伴",Pose(paused=True)),
           (350,75,"歪头看你",Pose(idle_frame=2,idle_weight=1)),
           (680,75,"梳理羽毛",Pose(idle_frame=4,idle_weight=1)),
           (20,365,"伸展翅膀",Pose(idle_frame=5,idle_weight=1)),
           (350,365,"轻盈飞行",Pose(motion="flying",flap_phase=.18,branch_alpha=0,pitch=-8)),
           (680,365,"回应鼠标",Pose(time=.2,reacting=True,motion_progress=.45,chirp=True)))
    for x,y,title,pose in poses:
        p.drawText(x+90,y-22,title)
        p.save()
        p.translate(x,y)
        renderer.paint(p,pose)
        p.restore()
    p.end()
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    if not preview.save(str(args.preview)):
        raise RuntimeError("Could not save preview")


if __name__ == "__main__":
    main()
