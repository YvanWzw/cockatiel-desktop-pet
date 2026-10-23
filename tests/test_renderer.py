import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtGui import QColor
from cockatiel_pet.renderer import CockatielRenderer, Pose


def test_transparency_clears_and_branch_only_when_requested():
    renderer = CockatielRenderer()
    resting = renderer.image(Pose(paused=True))
    flying = renderer.image(Pose(wing=0.8, branch_alpha=0))
    assert resting.pixelColor(0, 0).alpha() == 0
    assert resting.pixelColor(45, 185).alpha() > 0
    assert flying.pixelColor(45, 185).alpha() == 0
    assert resting.pixelColor(165, 94).red() > resting.pixelColor(165, 94).blue()


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
