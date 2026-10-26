import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QRect
from cockatiel_pet.renderer import CockatielRenderer, Pose


def pixels(image):
    return image.constBits().tobytes()


def orange_count(image, left, right):
    return sum(c.alpha()>128 and c.red()>c.green()*1.2 and c.red()>c.blue()*1.5
               for x in range(left,right) for y in range(72,102)
               for c in (image.pixelColor(x,y),))


def test_front_face_has_visible_orange_cheeks_on_both_sides():
    image=CockatielRenderer().image(Pose(paused=True))
    assert orange_count(image,110,132)>12
    assert orange_count(image,151,172)>12


def test_gripping_feet_and_branch_do_not_slide_during_idle_or_tracking():
    renderer=CockatielRenderer()
    for scale in (1,1.25,1.5,2):
        contact=QRect(round(70*scale),round(166*scale),round(140*scale),round(20*scale))
        for facing in (-1,1):
            base=pixels(renderer.image(Pose(paused=True,facing=facing),scale).copy(contact))
            for t,frame in ((.3,0),(1,2),(2.3,3),(5,4),(8,5)):
                image=renderer.image(Pose(time=t,facing=facing,idle_frame=frame,idle_weight=1,look=.8),scale)
                assert pixels(image.copy(contact))==base


def test_flight_is_one_complete_registered_cel_without_standing_body_or_branch():
    renderer=CockatielRenderer()
    for index,expected in enumerate(renderer.atlas.flight):
        actual=renderer.image(Pose(motion="flying",branch_alpha=0,flap_phase=(index+.1)/6),2)
        assert pixels(actual)==pixels(expected)
        assert actual.pixelColor(85,355).alpha()==0


def test_idle_moves_body_crest_and_tail_but_pause_is_identical():
    renderer=CockatielRenderer()
    a=renderer.image(Pose(time=.3),2)
    b=renderer.image(Pose(time=2.1),2)
    for area in (QRect(215,30,120,100),QRect(200,210,160,100),QRect(290,380,120,60)):
        assert pixels(a.copy(area))!=pixels(b.copy(area))
    assert pixels(renderer.image(Pose(time=0,paused=True)))==pixels(renderer.image(Pose(time=30,paused=True)))


def test_blink_replaces_only_eye_regions_without_washing_out_the_body():
    renderer=CockatielRenderer()
    renderer.image(Pose(blink=0))
    opened=renderer.resting_layer.copy()
    renderer.image(Pose(blink=1))
    closed=renderer.resting_layer
    assert pixels(opened.copy(QRect(230,140,100,30)))!=pixels(closed.copy(QRect(230,140,100,30)))
    assert pixels(opened.copy(QRect(0,200,560,280)))==pixels(closed.copy(QRect(0,200,560,280)))
    for x,y in ((245,150),(310,150),(280,240)):
        assert abs(opened.pixelColor(x,y).alpha()-closed.pixelColor(x,y).alpha())<3


def test_body_deformation_does_not_create_translucent_horizontal_bands():
    renderer=CockatielRenderer()
    for time in (0,.3,1,2,3):
        image=renderer.image(Pose(time=time))
        assert min(image.pixelColor(x,y).alpha() for x in range(130,150) for y in range(110,145))>245


def test_all_cels_fit_viewport_at_fractional_dpi_and_flight_extremes():
    renderer=CockatielRenderer()
    for scale in (1,1.25,1.5,2):
        for phase in (i/6 for i in range(6)):
            for facing,pitch in ((1,-15),(-1,15)):
                image=renderer.image(Pose(motion="flying",flap_phase=phase,lift=12,
                                         pitch=pitch,branch_alpha=0,facing=facing),scale)
                assert image.width()==round(280*scale)
                assert all(image.pixelColor(x,0).alpha()==0 and image.pixelColor(x,image.height()-1).alpha()==0 for x in range(image.width()))
                assert all(image.pixelColor(0,y).alpha()==0 and image.pixelColor(image.width()-1,y).alpha()==0 for y in range(image.height()))


def test_takeoff_and_landing_change_anatomy_at_contact_without_double_exposure():
    renderer=CockatielRenderer()
    assert not renderer.airborne(Pose(motion="takeoff",motion_progress=.23))
    assert renderer.airborne(Pose(motion="takeoff",motion_progress=.25))
    assert renderer.airborne(Pose(motion="landing",motion_progress=.75))
    assert not renderer.airborne(Pose(motion="landing",motion_progress=.77))
    assert not renderer.airborne(Pose(motion="flying",paused=True))
