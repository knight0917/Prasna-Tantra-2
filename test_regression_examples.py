import unittest
from datetime import datetime
from prasnatantra import PrasnaChart

# Regression expected positions under Raman Ayanamsha (calculated astronomically)
REGRESSION_DATA = {
    'Example I': {
        'dt': datetime(1950, 10, 20, 21, 0, 0),
        'lat': "12.9717",
        'lon': "77.5945",
        'tz': 5.5,
        'expected_lagna': 53.6591,
        'planets': {
            'Sun': 184.9497,
            'Moon': 305.3790,
            'Mercury': 176.7500,
            'Venus': 178.7742,
            'Mars': 235.9636,
            'Jupiter': 305.8871,
            'Saturn': 155.1461,
            'Rahu': 334.8929,
            'Ketu': 154.8929,
        }
    },
    'Example II': {
        'dt': datetime(1950, 3, 1, 20, 0, 0),
        'lat': "12.9717",
        'lon': "77.5945",
        'tz': 5.5,
        'expected_lagna': 162.1679,
        'planets': {
            'Sun': 318.7315,
            'Moon': 101.6584,
            'Mercury': 298.3712,
            'Venus': 282.8673,
            'Mars': 167.3916,
            'Jupiter': 298.8040,
            'Saturn': 144.7826,
            'Rahu': 347.2422,
            'Ketu': 167.2422,
        }
    },
    'Example III': {
        'dt': datetime(1947, 9, 9, 12, 25, 0),
        'lat': "12.9717",
        'lon': "77.5945",
        'tz': 5.5,
        'expected_lagna': 232.9647,
        'planets': {
            'Sun': 144.0751,
            'Moon': 68.7467,
            'Mercury': 153.8950,
            'Venus': 145.6216,
            'Mars': 85.2174,
            'Jupiter': 210.2809,
            'Saturn': 115.0787,
            'Rahu': 35.1638,
            'Ketu': 215.1638,
        }
    },
    'Example IV': {
        'dt': datetime(1942, 7, 1, 20, 15, 0),
        'lat': "18.97",
        'lon': "72.83",
        'tz': 5.5,
        'expected_lagna': 271.8935,
        'planets': {
            'Sun': 77.5106,
            'Moon': 300.7349,
            'Mercury': 57.3349,
            'Venus': 42.7211,
            'Mars': 109.1985,
            'Jupiter': 73.2188,
            'Saturn': 45.1800,
            'Rahu': 135.6194,
            'Ketu': 315.6194,
        }
    },
    'Example V': {
        'dt': datetime(1964, 5, 27, 18, 20, 0),
        'lat': "28.6",
        'lon': "77.2",
        'tz': 5.5,
        'expected_lagna': 214.2098,
        'planets': {
            'Sun': 44.3342,
            'Moon': 236.7041,
            'Mercury': 19.5856,
            'Venus': 74.8951,
            'Mars': 22.9039,
            'Jupiter': 18.7960,
            'Saturn': 312.8451,
            'Rahu': 71.6342,
            'Ketu': 251.6342,
        }
    },
    'Example VI': {
        'dt': datetime(1962, 11, 6, 9, 20, 0),
        'lat': "12.9717",
        'lon': "77.5945",
        'tz': 6.5,
        'expected_lagna': 229.2397,
        'planets': {
            'Sun': 201.3256,
            'Moon': 301.6964,
            'Mercury': 189.7678,
            'Venus': 211.9538,
            'Mars': 110.3182,
            'Jupiter': 311.0304,
            'Saturn': 283.5000,
            'Rahu': 101.7558,
            'Ketu': 281.7558,
        }
    },
    'Example VII': {
        'dt': datetime(1968, 9, 2, 14, 10, 0),
        'lat': "13.07",
        'lon': "80.28",
        'tz': 5.5,
        'expected_lagna': 253.6216,
        'planets': {
            'Sun': 137.9574,
            'Moon': 259.4372,
            'Mercury': 159.0048,
            'Venus': 158.1307,
            'Mars': 115.7589,
            'Jupiter': 142.9722,
            'Saturn': 2.9941,
            'Rahu': 349.0288,
            'Ketu': 169.0288,
        }
    },
    'Example VIII': {
        'dt': datetime(1942, 3, 14, 8, 15, 0),
        'lat': "12.9717",
        'lon': "77.5945",
        'tz': 5.5,
        'expected_lagna': 2.2599,
        'planets': {
            'Sun': 331.2894,
            'Moon': 295.7454,
            'Mercury': 304.7106,
            'Venus': 290.0619,
            'Mars': 42.3988,
            'Jupiter': 51.9433,
            'Saturn': 32.2414,
            'Rahu': 141.4221,
            'Ketu': 321.4221,
        }
    },
    'Example IX': {
        'dt': datetime(1963, 12, 1, 10, 15, 0),
        'lat': "12.9717",
        'lon': "77.5945",
        'tz': 5.5,
        'expected_lagna': 279.2519,
        'planets': {
            'Sun': 226.3588,
            'Moon': 49.2338,
            'Mercury': 240.6480,
            'Venus': 250.0374,
            'Mars': 244.9410,
            'Jupiter': 347.6667,
            'Saturn': 295.9120,
            'Rahu': 81.0847,
            'Ketu': 261.0847,
        }
    },
    'Example X': {
        'dt': datetime(1957, 3, 1, 10, 25, 0),
        'lat': "12.9717",
        'lon': "77.5945",
        'tz': 5.5,
        'expected_lagna': 24.7176,
        'planets': {
            'Sun': 318.5356,
            'Moon': 313.3937,
            'Mercury': 302.7621,
            'Venus': 307.3650,
            'Mars': 27.7196,
            'Jupiter': 157.1441,
            'Saturn': 232.0583,
            'Rahu': 211.7627,
            'Ketu': 31.7627,
        }
    },
    'Example XI': {
        'dt': datetime(1968, 12, 10, 10, 25, 0),
        'lat': "12.9717",
        'lon': "77.5945",
        'tz': 5.5,
        'expected_lagna': 291.9333,
        'planets': {
            'Sun': 236.2308,
            'Moon': 113.6051,
            'Mercury': 237.9525,
            'Venus': 278.3322,
            'Mars': 176.5781,
            'Jupiter': 161.5070,
            'Saturn': 356.8368,
            'Rahu': 343.7909,
            'Ketu': 163.7909,
        }
    },
    'Example XII': {
        'dt': datetime(1949, 5, 5, 14, 0, 0),
        'lat': "12.9717",
        'lon': "77.5945",
        'tz': 5.5,
        'expected_lagna': 136.5931,
        'planets': {
            'Sun': 22.8105,
            'Moon': 105.8493,
            'Mercury': 43.1003,
            'Venus': 27.6307,
            'Mars': 12.2284,
            'Jupiter': 280.1044,
            'Saturn': 127.6250,
            'Rahu': 3.1531,
            'Ketu': 183.1531,
        }
    },
}

class TestRamanRegression(unittest.TestCase):
    def test_all_examples_raman_positions(self):
        for name, data in REGRESSION_DATA.items():
            with self.subTest(example=name):
                # Construct PrasnaChart with Raman Ayanamsha
                chart = PrasnaChart(
                    local_datetime=data['dt'],
                    lat_str=data['lat'],
                    lon_str=data['lon'],
                    tz_offset_hours=data['tz'],
                    ayanamsha_mode="Raman"
                )
                
                # Check Lagna position
                diff_lagna = abs(chart.lagna_sidereal - data['expected_lagna'])
                if diff_lagna > 180:
                    diff_lagna = 360 - diff_lagna
                self.assertLess(
                    diff_lagna, 0.2,
                    f"{name} Lagna longitude mismatch: Cal {chart.lagna_sidereal:.4f}°, Exp {data['expected_lagna']:.4f}°"
                )
                
                # Check planet positions
                for p_name, expected_lon in data['planets'].items():
                    cal_lon = chart.planets[p_name]['longitude']
                    diff = abs(cal_lon - expected_lon)
                    if diff > 180:
                        diff = 360 - diff
                    self.assertLess(
                        diff, 0.2,
                        f"{name} {p_name} longitude mismatch: Cal {cal_lon:.4f}°, Exp {expected_lon:.4f}°"
                    )

if __name__ == "__main__":
    unittest.main()
