import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtGui import QColor
from cockatiel_pet.renderer import CockatielRenderer, Pose


def test_transparency_clears_and_branch_only_when_requested():
    renderer = CockatielRenderer()
    resting = renderer.image(Pose(paused=True))
    flying = renderer.image(Pose(wing=0.8, branch_alpha=0))
    assert resting.pixelColor(0, 0).alpha() == 0
    assert resting.pixelColor(45, 182).alpha() > 0
    assert flying.pixelColor(45, 182).alpha() == 0
    cheeks=[resting.pixelColor(x,y) for x in range(145,175) for y in range(75,102)]
    assert sum(c.alpha()>128 and c.red()>c.green()*1.2 and c.red()>c.blue()*1.5 for c in cheeks)>8


def test_preen_fully_replaces_neutral_pose_without_a_second_head():
    renderer=CockatielRenderer()
    renderer.image(Pose(idle_frame=4,idle_weight=1,branch_alpha=0))
    expected=renderer.atlas.frames[4]
    actual=renderer.resting_layer
    assert actual.constBits().tobytes()==expected.constBits().tobytes()


def test_bundled_artwork_and_wing_are_readable_and_premultiplied():
    renderer=CockatielRenderer()
    assert len(renderer.atlas.frames)==6
    assert renderer.atlas.image.hasAlphaChannel()
    assert not renderer.atlas.wing.isNull()
    assert renderer.atlas.image.pixelColor(0,0).alpha()==0


def test_head_blending_preserves_opacity_and_does_not_bleach_feathers():
    renderer=CockatielRenderer()
    renderer.image(Pose(reacting=True,motion_progress=.45))
    for x,y in ((150,90),(160,80),(145,100)):
        base=renderer.atlas.frames[0].pixelColor(x*2,y*2)
        target=renderer.atlas.frames[2].pixelColor(x*2,y*2)
        mixed=renderer.resting_layer.pixelColor(x*2,y*2)
        assert abs(mixed.alpha()-base.alpha())<=2
        for actual,a,b in zip(mixed.getRgb()[:3],base.getRgb()[:3],target.getRgb()[:3]):
            assert min(a,b)-2 <= actual <= max(a,b)+2


def test_all_poses_fit_transparent_viewport_at_fractional_dpi():
    renderer = CockatielRenderer()
    for scale in (1, 1.25, 1.5, 2):
        for wing in (0, 0.5, 1):
            image = renderer.image(Pose(wing=wing, lift=10, pitch=15, branch_alpha=0, facing=-1), scale)
            assert image.width() == round(280 * scale)
            for x in range(image.width()):
                assert image.pixelColor(x, 0).alpha() == 0
                assert image.pixelColor(x, image.height() - 1).alpha() == 0
            for y in range(image.height()):
                assert image.pixelColor(0, y).alpha() == 0
                assert image.pixelColor(image.width() - 1, y).alpha() == 0
