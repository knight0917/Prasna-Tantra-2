# Monkeypatch libephemeris to fix signature mismatches in horizons_backend where:
# 1. _rotate_equatorial_to_ecliptic is called with 2 arguments instead of 4
# 2. _cartesian_to_spherical is called with 1 argument instead of 3
# 3. _cartesian_velocity_to_spherical is called with 2 arguments instead of 6
try:
    import libephemeris.fast_calc as fc
    
    # 1. Patch _rotate_equatorial_to_ecliptic
    orig_rotate = fc._rotate_equatorial_to_ecliptic
    def patched_rotate(*args, **kwargs):
        if len(args) == 2:
            coords = args[0]
            eps = args[1]
            return orig_rotate(coords[0], coords[1], coords[2], eps)
        return orig_rotate(*args, **kwargs)
    fc._rotate_equatorial_to_ecliptic = patched_rotate
    
    # 2. Patch _cartesian_to_spherical
    orig_to_spherical = fc._cartesian_to_spherical
    def patched_to_spherical(*args, **kwargs):
        if len(args) == 1:
            pos = args[0]
            return orig_to_spherical(pos[0], pos[1], pos[2])
        return orig_to_spherical(*args, **kwargs)
    fc._cartesian_to_spherical = patched_to_spherical
    
    # 3. Patch _cartesian_velocity_to_spherical
    orig_vel_to_spherical = fc._cartesian_velocity_to_spherical
    def patched_vel_to_spherical(*args, **kwargs):
        if len(args) == 2:
            pos = args[0]
            vel = args[1]
            return orig_vel_to_spherical(pos[0], pos[1], pos[2], vel[0], vel[1], vel[2])
        return orig_vel_to_spherical(*args, **kwargs)
    fc._cartesian_velocity_to_spherical = patched_vel_to_spherical
    
    try:
        import libephemeris.horizons_backend as hb
        hb._rotate_equatorial_to_ecliptic = patched_rotate
        hb._cartesian_to_spherical = patched_to_spherical
        hb._cartesian_velocity_to_spherical = patched_vel_to_spherical
    except ImportError:
        pass
    try:
        import libephemeris.fixed_stars as fs
        fs._rotate_equatorial_to_ecliptic = patched_rotate
        fs._cartesian_to_spherical = patched_to_spherical
        fs._cartesian_velocity_to_spherical = patched_vel_to_spherical
    except ImportError:
        pass
except ImportError:
    pass

from .engine import PrasnaChart, SIGN_LORDS
from .astronomy import get_sign_name
