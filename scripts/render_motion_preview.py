"""Export the actual renderer's animation for review; Pillow is a dev dependency."""
import argparse
import math
import os
from pathlib import Path
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage,QPainter,QColor,QFont,QFontDatabase
from PySide6.QtWidgets import QApplication
from cockatiel_pet.renderer import CockatielRenderer,Pose
from cockatiel_pet.animation import gesture_weight


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=Path("docs/motion-preview.gif"))
    args=parser.parse_args()
    app=QApplication([])
    fontpath=Path(os.environ.get("WINDIR","C:/Windows"))/"Fonts"/"msyh.ttc"
    if fontpath.is_file():QFontDatabase.addApplicationFont(str(fontpath))
    renderer=CockatielRenderer()
    frames=[]
    for index in range(132):
        t=index/20
        quiet=Pose(time=t)
        if .5<t<1.8:
            quiet.idle_frame,quiet.idle_weight=2,gesture_weight((t-.5)/1.3)
        elif 2.15<t<4.5:
            quiet.idle_frame,quiet.idle_weight=4,gesture_weight((t-2.15)/2.35)
        elif 4.8<t<6.4:
            quiet.idle_frame,quiet.idle_weight=5,gesture_weight((t-4.8)/1.6)
        quiet.blink=math.sin(math.pi*(t-1.9)/.16)**2 if 1.9<=t<=2.06 else 0
        flying=Pose(time=t,motion="flying",flap_phase=(t*6)%1,branch_alpha=0,pitch=math.sin(t*2)*4)
        phase=t%3
        reaction=Pose(time=t,look=math.sin(t)*.5,reacting=phase<1.0,motion_progress=phase,chirp=phase<.4)
        canvas=QImage(960,330,QImage.Format.Format_ARGB32_Premultiplied)
        canvas.fill(QColor("#f1f2ee"))
        p=QPainter(canvas)
        p.setFont(QFont("Microsoft YaHei",11))
        p.setPen(QColor("#35404a"))
        for x,title,pose in ((20,"眨眼 · 歪头 · 理毛 · 伸展",quiet),(340,"固定身体，连续振翅",flying),(660,"靠近与点击时轻柔回应",reaction)):
            p.drawText(x+35,35,title)
            p.save();p.translate(x,65);renderer.paint(p,pose);p.restore()
        p.end()
        canvas=canvas.convertToFormat(QImage.Format.Format_RGBA8888)
        frames.append(Image.frombytes("RGBA",(960,330),canvas.constBits().tobytes()).convert("RGB"))
    palette=frames[0].quantize(colors=192)
    encoded=[frame.quantize(palette=palette,dither=Image.Dither.NONE) for frame in frames]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    encoded[0].save(args.output,save_all=True,append_images=encoded[1:],duration=50,loop=0,optimize=True,disposal=2)
    print(args.output)


if __name__=="__main__":main()
