# Monkeypatch libephemeris to fix signature mismatches in horizons_backend where:
# 1. _rotate_equatorial_to_ecliptic is called with 2 arguments instead of 4
# 2. _cartesian_to_spherical is called with 1 argument instead of 3
# 3. _cartesian_velocity_to_spherical is called with 2 arguments instead of 6
# Also fix a packaging error in libephemeris version 2.0.0 where horizons_backend.py
# attempts to do "from .ayanamsha import get_ayanamsha_ut", but the ayanamsha module does
# not exist. We bind get_ayanamsha_ut to return the true/appropriate ayanamsha (mean + nutation).
# Also fix the Schwarzschild radius calculation (speed of light unit conversion bug) in _apply_deflection_horizons.

try:
    import sys
    import types
    import libephemeris
    
    # 1. Patch virtual libephemeris.ayanamsha module
    def patched_get_ayanamsha_ut(jd_tt):
        from libephemeris.time_utils import deltat
        jd_ut = jd_tt - deltat(jd_tt)
        from libephemeris.planets import _get_ayanamsa_for_flags
        return _get_ayanamsa_for_flags(jd_ut, 0)

    ayanamsha_mod = types.ModuleType("libephemeris.ayanamsha")
    ayanamsha_mod.get_ayanamsha_ut = patched_get_ayanamsha_ut
    sys.modules["libephemeris.ayanamsha"] = ayanamsha_mod
    libephemeris.ayanamsha = ayanamsha_mod

    import libephemeris.fast_calc as fc
    
    # 2. Patch _rotate_equatorial_to_ecliptic
    if not getattr(fc._rotate_equatorial_to_ecliptic, "_is_patched", False):
        orig_rotate = fc._rotate_equatorial_to_ecliptic
        def patched_rotate(*args, **kwargs):
            if len(args) == 2:
                coords = args[0]
                eps = args[1]
                return orig_rotate(coords[0], coords[1], coords[2], eps)
            return orig_rotate(*args, **kwargs)
        patched_rotate._is_patched = True
        fc._rotate_equatorial_to_ecliptic = patched_rotate
    else:
        patched_rotate = fc._rotate_equatorial_to_ecliptic
    
    # 3. Patch _cartesian_to_spherical
    if not getattr(fc._cartesian_to_spherical, "_is_patched", False):
        orig_to_spherical = fc._cartesian_to_spherical
        def patched_to_spherical(*args, **kwargs):
            if len(args) == 1:
                pos = args[0]
                return orig_to_spherical(pos[0], pos[1], pos[2])
            return orig_to_spherical(*args, **kwargs)
        patched_to_spherical._is_patched = True
        fc._cartesian_to_spherical = patched_to_spherical
    else:
        patched_to_spherical = fc._cartesian_to_spherical
    
    # 4. Patch _cartesian_velocity_to_spherical
    if not getattr(fc._cartesian_velocity_to_spherical, "_is_patched", False):
        orig_vel_to_spherical = fc._cartesian_velocity_to_spherical
        def patched_vel_to_spherical(*args, **kwargs):
            if len(args) == 2:
                pos = args[0]
                vel = args[1]
                return orig_vel_to_spherical(pos[0], pos[1], pos[2], vel[0], vel[1], vel[2])
            return orig_vel_to_spherical(*args, **kwargs)
        patched_vel_to_spherical._is_patched = True
        fc._cartesian_velocity_to_spherical = patched_vel_to_spherical
    else:
        patched_vel_to_spherical = fc._cartesian_velocity_to_spherical
    
    try:
        import libephemeris.horizons_backend as hb
        
        # 5. Patch HorizonsClient.fetch_state_vector to use REF_PLANE='FRAME' with REF_SYSTEM='ICRF'
        if not getattr(hb.HorizonsClient.fetch_state_vector, "_is_patched", False):
            def patched_fetch_state_vector(self, command: str, jd: float, center: str = "@0", time_type: str = "TDB"):
                cache_key = (round(jd, 12), command, center)
                with self._cache_lock:
                    if cache_key in self._cache:
                        self._cache.move_to_end(cache_key)
                        return self._cache[cache_key]

                # Build URL with correct REF_PLANE parameter
                params = {
                    "format": "json",
                    "COMMAND": f"'{command}'",
                    "EPHEM_TYPE": "'VECTORS'",
                    "CENTER": f"'{center}'",
                    "TLIST": str(jd),
                    "TLIST_TYPE": "'JD'",
                    "VEC_TABLE": "'2'",
                    "OUT_UNITS": "'AU-D'",
                    "VEC_CORR": "'NONE'",
                    "CSV_FORMAT": "'YES'",
                    "REF_SYSTEM": "'ICRF'",
                    "REF_PLANE": "'FRAME'",
                    "TIME_TYPE": f"'{time_type}'",
                }
                query = "&".join(f"{k}={v}" for k, v in params.items())
                url = f"{hb.API_URL}?{query}"

                # Fetch with retry
                sv = self._fetch_with_retry(url, command)

                with self._cache_lock:
                    self._cache[cache_key] = sv
                    if len(self._cache) > self._max_cache_size:
                        self._cache.popitem(last=False)

                return sv
            patched_fetch_state_vector._is_patched = True
            hb.HorizonsClient.fetch_state_vector = patched_fetch_state_vector

        hb._rotate_equatorial_to_ecliptic = patched_rotate
        hb._cartesian_to_spherical = patched_to_spherical
        hb._cartesian_velocity_to_spherical = patched_vel_to_spherical

        # 6. Patch _apply_deflection_horizons to fix the Schwarzschild radius calculation (speed of light unit conversion bug)
        if not getattr(hb._apply_deflection_horizons, "_is_patched", False):
            def patched_apply_deflection_horizons(
                geo,
                earth_bary,
                jd_tt,
                light_time,
                batch,
            ):
                import math
                c_speed = 299792.458
                deflectors = [
                    ("10", 1.32712440041279419e11),  # Sun GM
                    ("5", 1.26712764945480000e8),  # Jupiter GM
                    ("6", 3.79406260288322009e7),  # Saturn GM
                ]
                result = list(geo)
                for defl_cmd, gm in deflectors:
                    key = (defl_cmd, jd_tt, "@0")
                    if key not in batch:
                        continue
                    defl_sv = batch[key]
                    defl_pos = defl_sv.pos
                    e = (
                        defl_pos[0] - earth_bary[0],
                        defl_pos[1] - earth_bary[1],
                        defl_pos[2] - earth_bary[2],
                    )
                    e_dist = math.sqrt(e[0] ** 2 + e[1] ** 2 + e[2] ** 2)
                    q = (
                        result[0] - e[0],
                        result[1] - e[1],
                        result[2] - e[2],
                    )
                    q_dist = math.sqrt(q[0] ** 2 + q[1] ** 2 + q[2] ** 2)
                    geo_dist = math.sqrt(result[0] ** 2 + result[1] ** 2 + result[2] ** 2)
                    if e_dist < 1e-20 or q_dist < 1e-20 or geo_dist < 1e-20:
                        continue
                    two_gm_c2 = 2.0 * gm / (c_speed * c_speed * 1.495978707e8)  # km -> AU
                    dot_eq = (result[0] * e[0] + result[1] * e[1] + result[2] * e[2]) / (
                        geo_dist * e_dist
                    )
                    if dot_eq > 0.9999:
                        continue
                    factor = two_gm_c2 / (e_dist * (1.0 + dot_eq + 1e-30))
                    for i in range(3):
                        unit_geo_i = result[i] / geo_dist
                        unit_e_i = e[i] / e_dist
                        result[i] += factor * (unit_geo_i - dot_eq * unit_e_i)
                return tuple(result)
            patched_apply_deflection_horizons._is_patched = True
            hb._apply_deflection_horizons = patched_apply_deflection_horizons

        # 7. Patch _calc_analytical to add nutation in longitude (dpsi) for mean nodes/apogees
        if not getattr(hb._calc_analytical, "_is_patched", False):
            def patched_calc_analytical(jd_ut, body_id, iflag):
                from libephemeris.time_utils import deltat
                from libephemeris.constants import FLG_SPEED, FLG_SIDEREAL, FLG_NONUT, FLG_EQUATORIAL
                import math

                jd_tt = jd_ut + deltat(jd_ut)

                if body_id == 10:  # Mean Node
                    from libephemeris.lunar import calc_mean_lunar_node
                    lon = calc_mean_lunar_node(jd_tt)
                    lat = 0.0
                    dist = 0.002569
                elif body_id == 12:  # Mean Apogee (Lilith)
                    from libephemeris.lunar import calc_mean_lilith_with_latitude
                    lon, lat = calc_mean_lilith_with_latitude(jd_tt)
                    dist = 0.002710
                else:
                    raise KeyError(f"Body {body_id} not analytical")

                _sid_eq = bool(iflag & FLG_SIDEREAL) and bool(iflag & FLG_EQUATORIAL)
                if not (iflag & FLG_NONUT) and not _sid_eq:
                    from libephemeris.cache import get_cached_nutation
                    dpsi_rad, _ = get_cached_nutation(jd_tt)
                    lon = (lon + math.degrees(dpsi_rad)) % 360.0

                # Speed via finite difference
                dt = 1.0 / 86400.0  # 1 second
                if body_id == 10:
                    from libephemeris.lunar import calc_mean_lunar_node
                    lon2 = calc_mean_lunar_node(jd_tt + dt)
                    if not (iflag & FLG_NONUT) and not _sid_eq:
                        from libephemeris.cache import get_cached_nutation
                        dpsi_rad2, _ = get_cached_nutation(jd_tt + dt)
                        lon2 = (lon2 + math.degrees(dpsi_rad2)) % 360.0
                    dlon = (lon2 - lon) / dt
                    if abs(dlon) > 180 / dt:
                        dlon = ((lon2 - lon + 180) % 360 - 180) / dt
                elif body_id == 12:
                    from libephemeris.lunar import calc_mean_lilith_with_latitude
                    lon2, lat2 = calc_mean_lilith_with_latitude(jd_tt + dt)
                    if not (iflag & FLG_NONUT) and not _sid_eq:
                        from libephemeris.cache import get_cached_nutation
                        dpsi_rad2, _ = get_cached_nutation(jd_tt + dt)
                        lon2 = (lon2 + math.degrees(dpsi_rad2)) % 360.0
                    dlon = ((lon2 - lon + 180) % 360 - 180) / dt
                else:
                    dlon = 0.0

                # Sidereal correction
                if iflag & FLG_SIDEREAL:
                    from libephemeris.ayanamsha import get_ayanamsha_ut
                    ayan = get_ayanamsha_ut(jd_tt)
                    lon = (lon - ayan) % 360.0

                return ((lon, lat, dist, dlon, 0.0, 0.0), iflag)
            patched_calc_analytical._is_patched = True
            hb._calc_analytical = patched_calc_analytical

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
