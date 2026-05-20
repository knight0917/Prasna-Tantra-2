# Monkeypatch libephemeris to fix a bug in horizons_backend where
# _rotate_equatorial_to_ecliptic is called with only 2 arguments instead of 4.
try:
    import libephemeris.fast_calc as fc
    orig_rotate = fc._rotate_equatorial_to_ecliptic
    
    def patched_rotate(*args, **kwargs):
        if len(args) == 2:
            coords = args[0]
            eps = args[1]
            return orig_rotate(coords[0], coords[1], coords[2], eps)
        return orig_rotate(*args, **kwargs)
        
    fc._rotate_equatorial_to_ecliptic = patched_rotate
    
    try:
        import libephemeris.horizons_backend as hb
        hb._rotate_equatorial_to_ecliptic = patched_rotate
    except ImportError:
        pass
    try:
        import libephemeris.fixed_stars as fs
        fs._rotate_equatorial_to_ecliptic = patched_rotate
    except ImportError:
        pass
except ImportError:
    pass

from .engine import PrasnaChart, SIGN_LORDS
from .astronomy import get_sign_name
