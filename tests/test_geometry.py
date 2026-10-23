import pytest
from cockatiel_pet.models import Point, Rect, FOOT, BRANCH_TOP, perch_bounds, effective_scale, surface_origin, to_local


@pytest.mark.parametrize("work,dpi", [(Rect(0,0,1920,1040),1), (Rect(-1920,-600,0,440),1.25), (Rect(0,0,3840,2088),1.5), (Rect(0,0,320,240),2)])
def test_surface_fits_and_dpi_roundtrip(work,dpi):
    s = effective_scale(work,dpi,1)
    b = perch_bounds(work,s)
    for p in (Point(b.left,b.top),Point(b.right,b.bottom)):
        origin = surface_origin(p,s)
        assert work.contains(origin)
        assert work.contains(origin+Point(280,240)*s)
        assert to_local(p,p,s).distance(FOOT) < 1e-8
    assert FOOT.y == BRANCH_TOP
