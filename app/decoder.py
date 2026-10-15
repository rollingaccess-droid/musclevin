"""Classic American muscle-car VIN + trim tag decoder (1964-1980), phase-1 prototype.

Rules come only from public documentation; see README.md "Sources" (S1..S12).
Every field carries the source id it was decoded from.
Pure standard library. Usage:  python decoder.py <VIN> [--year 1969] [--tag "ST 69-13637 ..."]
"""
from __future__ import annotations
import json, re, sys
from dataclasses import dataclass, field, asdict

# ----------------------------------------------------------------- tables
GM_DIVISION = {"1": "Chevrolet", "2": "Pontiac"}

# Chevrolet 1965-71: positions 2-3 series. Odd = 6-cyl, even = V8 (S1, S2)
CHEV_SERIES_6571 = {
    "31": ("Chevelle 300", 6), "32": ("Chevelle 300", 8),
    "33": ("Chevelle 300 Deluxe / Nomad / Greenbrier", 6), "34": ("Chevelle 300 Deluxe / Nomad / Greenbrier", 8),
    "35": ("Chevelle Malibu", 6), "36": ("Chevelle Malibu", 8),
    "37": ("Chevelle Malibu SS (1965 only)", 6), "38": ("Chevelle Malibu SS / SS 396 (1965-68); Concours wagon (1969+)", 8),
    "23": ("Camaro (1967-71)", 6), "24": ("Camaro (1967-71)", 8),
    "11": ("Chevy II 100 / Nova", 6), "13": ("Chevy II / Nova", 6), "14": ("Chevy II / Nova", 8),
    "15": ("Chevy II Nova (1965-67)", 6), "16": ("Chevy II Nova (1965-67)", 8),
    "17": ("Chevy II Nova SS (1965-67)", 6), "18": ("Chevy II Nova SS (1965-67)", 8),
    "94": ("Corvette", 8),
}
CHEV_SERIES_7280 = {  # S3, S4
    "B": "Nomad", "C": "Chevelle / El Camino / Greenbrier", "D": "Chevelle Malibu / Custom El Camino / Concours",
    "E": "Chevelle Laguna", "G": "Chevelle Malibu Estate", "H": "Monte Carlo / Concours Estate / Laguna Estate",
    "K": "Biscayne / Brookwood / Bel Air", "L": "Bel Air / Townsman / Impala", "M": "Impala / Kingswood / Monza",
    "N": "Caprice / Kingswood Estate", "Q": "Camaro (1972-79)", "P": "Camaro (1980)", "S": "Camaro Type LT / Berlinetta",
    "R": "Monza 2+2", "V": "Vega", "X": "Nova", "Y": "Nova Custom / Concours", "Z": "Corvette",
}
GM_BODY = {  # S1, S2, S6
    "07": "2-door sedan (post)", "11": "2-door sedan (post)", "17": "2-door coupe / hatchback", "27": "2-door coupe (post)",
    "35": "4-door station wagon, 2-seat", "36": "4-door wagon, dual-action tailgate", "37": "2-door sport coupe (hardtop)",
    "39": "4-door sport sedan (hardtop)", "46": "4-door wagon, 3-seat", "47": "2-door hardtop coupe",
    "67": "2-door convertible", "69": "4-door sedan", "80": "2-door sedan pickup (El Camino)", "87": "2-door sport coupe",
}
CHEV_PLANTS = {  # S1, S3
    "A": "Atlanta (Lakewood), GA", "B": "Baltimore, MD", "C": "South Gate, CA", "D": "Doraville, GA", "F": "Flint, MI",
    "G": "Framingham, MA", "H": "Fremont, CA (1964)", "J": "Janesville, WI", "K": "Kansas City (Leeds), MO",
    "L": "Van Nuys (Los Angeles), CA", "N": "Norwood, OH", "R": "Arlington, TX", "S": "St. Louis, MO",
    "T": "Tarrytown, NY", "U": "Lordstown, OH", "W": "Willow Run, MI", "Y": "Wilmington, DE", "Z": "Fremont, CA",
    "0": "Oshawa, ON, Canada (1972+)", "1": "Oshawa, ON (pre-1972) / Ste. Therese, QC, Canada", "2": "Ste. Therese, QC, Canada",
}
PONT_SERIES_6571 = {  # S5, S6, S7
    "33": "Tempest (LeMans T-37 in 1971)", "35": "Tempest Custom (LeMans in 1971)", "37": "Tempest LeMans (LeMans Sport in 1971)",
    "39": "Tempest Safari", "42": "GTO (1966-71)", "52": "Catalina",
    "23": "Firebird (6-cyl 1967-69 / base 1970-71)", "24": "Firebird V8 (1967-69) / Esprit (1970-71)",
    "26": "Firebird Formula (1970-71)", "28": "Firebird Trans Am (1970-71)",
}
PONT_PLANTS = {  # S5, S6
    "A": "Atlanta, GA", "B": "Baltimore, MD", "C": "South Gate, CA", "D": "Doraville, GA", "E": "Linden, NJ",
    "G": "Framingham, MA", "K": "Kansas City, MO", "L": "Van Nuys, CA", "N": "Norwood, OH", "P": "Pontiac, MI",
    "R": "Arlington, TX", "U": "Lordstown, OH", "V": "Bloomfield, IL", "W": "Willow Run, MI", "X": "Kansas City, KS",
    "Z": "Fremont, CA", "1": "Oshawa, ON, Canada", "2": "Ste. Therese, QC, Canada",
}
CHEV_ENGINE_1972 = {  # S3, S4
    "B": "140 L4 1/2-bbl", "D": "250 L6 1-bbl", "F": "307 V8 2-bbl", "H": "350 V8 2-bbl", "J": "350 V8 4-bbl (L48)",
    "K": "350 V8 4-bbl", "L": "350 V8 4-bbl (255 net hp)", "R": "400 V8 2-bbl", "S": "402 V8 4-bbl (LS3, single exh.)",
    "U": "402 V8 4-bbl (LS3)", "V": "454 V8 4-bbl (LS5)", "W": "454 V8 4-bbl (LS5, dual exh.)",
}
CHEV_ENGINE_7380 = {  # S3, S8 (model-specific exceptions exist)
    "A": "140 L4 1-bbl (231 V6 in 1980)", "B": "140 L4 2-bbl", "D": "250 L6 1-bbl", "F": "307 V8 2-bbl", "G": "262/305 V8 2-bbl",
    "H": "350 V8 2-bbl (305 V8 in 1980)", "K": "350 V8 4-bbl (229 V6 in 1980)", "L": "350 V8 4-bbl", "Q": "305 V8 2-bbl (1976)",
    "R": "400 V8 2-bbl", "T": "350 V8 4-bbl (Z28 / L82)", "U": "305 V8 2-bbl", "X": "454 V8 4-bbl", "Y": "454 V8 4-bbl",
}

# Ford / Mercury 1965-79, 11 characters (S9, S10, S11)
FORD_PLANTS = {
    "A": "Atlanta, GA", "B": "Oakville, ON, Canada", "C": "Chester, PA", "D": "Dallas, TX", "E": "Mahwah, NJ",
    "F": "Dearborn, MI", "G": "Chicago, IL", "H": "Lorain, OH", "J": "Los Angeles, CA", "K": "Kansas City", "L": "Michigan Truck",
    "N": "Norfolk, VA", "P": "Twin Cities, MN", "R": "San Jose, CA", "S": "Allen Park Pilot Plant, MI", "T": "Metuchen, NJ",
    "U": "Louisville, KY", "W": "Wayne, MI", "X": "St. Thomas, ON, Canada", "Y": "Wixom, MI", "Z": "St. Louis, MO",
}
FORD_BODY = {  # code -> [(first_year, last_year, meaning, source)]; Mustang/Cougar (S9), Fairlane/Torino (S16), Galaxie (S17)
    "07": [(1965, 1966, "Mustang 2-door hardtop", "S9")], "08": [(1965, 1966, "Mustang convertible", "S9")],
    "09": [(1965, 1966, "Mustang 2+2 fastback", "S9")],
    "01": [(1967, 1973, "Mustang 2-door hardtop", "S9")], "02": [(1967, 1973, "Mustang fastback / SportsRoof (incl. Mach 1, Boss pre-1970)", "S9")],
    "03": [(1967, 1973, "Mustang convertible", "S9")], "04": [(1969, 1973, "Mustang Grande hardtop", "S9")],
    "05": [(1970, 1973, "Mustang Mach 1 SportsRoof", "S9")],
    "91": [(1967, 1973, "Mercury Cougar 2-door hardtop", "S9")], "93": [(1967, 1973, "Mercury Cougar XR-7 2-door hardtop", "S9")],
}
_FORD_INTERMEDIATE = {  # S16 ford-torino.de VIN decoder pages, model years 1968, 1969, 1970, 1971
    (1968, 1969): {"30": "Fairlane 2-door hardtop", "31": "Fairlane 4-door sedan", "32": "Fairlane 4-door station wagon",
                   "33": "Fairlane 500 2-door hardtop", "34": "Fairlane 500 4-door sedan", "35": "Fairlane 500 2-door fastback",
                   "36": "Fairlane 500 2-door convertible", "37": "Fairlane 500 4-door station wagon", "38": "Torino Squire 4-door station wagon",
                   "40": "Torino 2-door hardtop", "41": "Torino 4-door sedan", "42": "Torino GT 2-door fastback",
                   "43": "Torino GT 2-door convertible", "44": "Torino GT 2-door hardtop",
                   "47": "Ranchero 2-door pickup", "48": "Ranchero 500 2-door pickup", "49": "Ranchero GT 2-door pickup"},
    (1969, 1969): {"45": "Torino Cobra (Fairlane Cobra) 2-door hardtop", "46": "Torino Cobra (Fairlane Cobra) 2-door fastback"},
    (1970, 1970): {"28": "Fairlane 500 4-door sedan", "29": "Fairlane 500 2-door hardtop", "30": "Torino 2-door hardtop",
                   "31": "Torino 4-door sedan", "32": "Torino 4-door hardtop", "33": "Torino Brougham 2-door hardtop",
                   "34": "Torino 2-door fastback (SportsRoof)", "35": "Torino GT 2-door fastback (SportsRoof)",
                   "36": "Torino Brougham 4-door hardtop", "37": "Torino GT 2-door convertible", "38": "Torino Cobra 2-door fastback (SportsRoof)",
                   "41": "Fairlane 500 4-door station wagon", "42": "Torino 4-door station wagon", "43": "Torino Squire 4-door station wagon"},
    (1971, 1971): {"25": "Torino 2-door hardtop", "27": "Torino 4-door sedan", "30": "Torino 500 2-door hardtop",
                   "31": "Torino 500 4-door sedan", "32": "Torino 500 4-door hardtop", "33": "Torino Brougham 2-door hardtop",
                   "34": "Torino 500 2-door fastback (SportsRoof)", "35": "Torino GT 2-door fastback (SportsRoof)",
                   "36": "Torino Brougham 4-door hardtop", "37": "Torino GT 2-door convertible", "38": "Torino Cobra 2-door fastback (SportsRoof)",
                   "40": "Torino 4-door station wagon", "42": "Torino 500 4-door station wagon", "43": "Torino Squire 4-door station wagon"},
}
_FORD_FULLSIZE_1968 = {  # S17 mercurystuff.com 1968 Ford & Mercury identification (body serial codes)
    "50": "Custom 2-door sedan", "51": "Custom 4-door sedan", "52": "Custom 500 2-door sedan", "53": "Custom 500 4-door sedan",
    "54": "Galaxie 500 4-door sedan", "55": "Galaxie 500 2-door hardtop (fastback)", "56": "Galaxie 500 4-door hardtop",
    "57": "Galaxie 500 2-door convertible", "58": "Galaxie 500 2-door hardtop (formal roof)",
    "60": "Galaxie 500 XL 2-door hardtop (fastback)", "61": "Galaxie 500 XL 2-door convertible",
    "62": "LTD 2-door hardtop", "64": "LTD 4-door sedan", "66": "LTD 4-door hardtop",
    "70": "Ranch Wagon 4-door, 6-pass.", "71": "Custom Ranch Wagon 4-door, 6-pass.", "72": "Custom Ranch Wagon 4-door, 10-pass.",
    "73": "Country Sedan 4-door, 6-pass.", "74": "Country Sedan 4-door, 10-pass.", "75": "Country Squire 4-door, 6-pass.",
    "76": "Country Squire 4-door, 10-pass.",
}
for (a, z), tbl in _FORD_INTERMEDIATE.items():
    for k, v in tbl.items(): FORD_BODY.setdefault(k, []).append((a, z, v, "S16"))
for k, v in _FORD_FULLSIZE_1968.items(): FORD_BODY.setdefault(k, []).append((1968, 1968, v, "S17"))

def ford_body(code, y):
    """Return (meaning, source) for a Ford body serial code in model year y, or (None, None)."""
    for a, z, txt, src in FORD_BODY.get(code, []):
        if y and a <= y <= z: return txt, src
    return None, None

FORD_ENGINE = {  # (first_year, last_year, meaning)  S9, S11
    "T": [(1965, 1970, "200 L6 1-bbl")], "U": [(1965, 1970, "170/250 L6 1-bbl")],
    "C": [(1965, 1968, "289 V8 2-bbl"), (1970, 1971, "429 Cobra Jet V8 4-bbl")], "A": [(1965, 1967, "289 V8 4-bbl")], "K": [(1965, 1967, "289 V8 4-bbl High Performance (K-code)")],
    "F": [(1968, 1973, "302 V8 2-bbl")], "J": [(1968, 1968, "302 V8 4-bbl"), (1970, 1971, "429 Cobra Jet Ram Air V8 4-bbl")], "G": [(1969, 1970, "Boss 302 V8 4-bbl")],
    "H": [(1969, 1969, "351W V8 2-bbl"), (1970, 1973, "351 V8 2-bbl")], "M": [(1969, 1973, "351 V8 4-bbl")],
    "S": [(1967, 1970, "390 V8 4-bbl GT")], "Y": [(1968, 1969, "390 V8 2-bbl")], "W": [(1968, 1968, "427 V8 4-bbl")],
    "R": [(1968, 1970, "428 Cobra Jet V8, Ram Air")], "Q": [(1968, 1970, "428 Cobra Jet V8 (non-Ram Air) / 428 SCJ w/ option"), (1971, 1973, "351 Cobra Jet V8 4-bbl")],
    "Z": [(1969, 1970, "Boss 429 V8 4-bbl")],
    "L": [(1970, 1973, "250 L6 1-bbl")], "N": [(1970, 1971, "429 V8 4-bbl Thunder Jet")],
    "X": [(1968, 1968, "390 V8 2-bbl premium fuel")], "6": [(1968, 1968, "302 V8 2-bbl low compression")],
    "2": [(1968, 1968, "200 L6 1-bbl low compression")],
}

# Mopar 1968-74, 13 characters (S12, S13, S14)
MOPAR_LINE = {  # S12/S18; J only 1970+, X (Charger) through 1970, W covers Charger from 1971
    "B": "Plymouth Barracuda", "R": "Plymouth Belvedere / Satellite / Road Runner / GTX", "V": "Plymouth Valiant / Duster",
    "P": "Plymouth Fury", "L": "Dodge Dart", "W": "Dodge Coronet / Super Bee (Charger from 1971)", "X": "Dodge Charger (to 1970)",
    "J": "Dodge Challenger (1970+)", "D": "Dodge Polara / Monaco", "C": "Chrysler", "Y": "Imperial",
}
MOPAR_CLASS = {"E": "Economy", "L": "Low", "M": "Medium", "H": "High", "P": "Premium", "S": "Special",
               "K": "Police", "T": "Taxi", "N": "New York taxi", "G": "New York / Dodge taxi (1972+)",
               "O": "Super Stock (1966-67)", "X": "Fast-top (special)"}
MOPAR_MODELNAME = {  # 1969 two-letter car line + price class (S15)
    "BH": "Barracuda", "BS": "Barracuda 'Cuda / Formula S", "RL": "Belvedere", "RM": "Road Runner", "RH": "Satellite",
    "RP": "Sport Satellite", "RS": "GTX", "WL": "Coronet Deluxe", "WM": "Coronet Super Bee", "WH": "Coronet 440",
    "WP": "Coronet 500", "WS": "Coronet R/T", "LL": "Dart / Swinger", "LM": "Dart Swinger 340", "LP": "Dart GT",
    "LS": "Dart GTS", "LH": "Dart Custom", "XH": "Charger", "XP": "Charger (SE)", "XS": "Charger R/T",
    "XX": "Charger 500 / Charger Daytona", "JH": "Challenger", "JS": "Challenger R/T",
}
MOPAR_BODY = {"21": "2-door sedan (post)", "23": "2-door hardtop", "27": "2-door convertible", "29": "2-door sports hardtop",
              "41": "4-door sedan", "43": "4-door hardtop", "45": "4-door wagon, 6-pass.", "46": "4-door wagon, 9-pass."}
# 5th-character engine codes by model year (S18 Lee Herman table via degeneratepress.com; 1969-71 also S12/S19)
_M_6869 = {"A": "170 L6 1-bbl", "B": "225 L6 1-bbl", "C": "special-order 6-cyl", "D": "273 V8 2-bbl",
           "F": "318 V8 2-bbl", "G": "383 V8 2-bbl", "H": "383 V8 4-bbl High Performance", "J": "426 Hemi V8 2x4-bbl",
           "K": "440 V8 4-bbl", "L": "440 V8 4-bbl High Performance",
           "M": "special-order 8-cyl (also used on 1969-1/2 440 Six Pack/Six Barrel A12 cars)",
           "P": "340 V8 4-bbl High Performance"}
_M_7071 = {"B": "198 L6 1-bbl", "C": "225 L6 1-bbl", "E": "special-order 6-cyl", "G": "318 V8 2-bbl",
           "H": "340 V8 4-bbl High Performance", "K": "360 V8 2-bbl", "L": "383 V8 2-bbl",
           "N": "383 V8 4-bbl High Performance", "R": "426 Hemi V8 2x4-bbl", "T": "440 V8 4-bbl",
           "U": "440 V8 4-bbl High Performance", "V": "440 V8 3x2-bbl (Six Pack / Six Barrel)", "Z": "special-order 8-cyl"}
MOPAR_ENGINE = {
    1966: {"A": "170 L6 1-bbl", "B": "225 L6 1-bbl", "C": "special-order 6-cyl", "D": "273 V8 2-bbl", "E": "318 V8 2-bbl",
           "F": "361 V8 2-bbl", "G": "383 V8 2-bbl", "H": "426 Hemi V8 2x4-bbl", "J": "440 V8 4-bbl", "K": "special-order 8-cyl"},
    1967: {"A": "170 L6 1-bbl", "B": "225 L6 1-bbl", "C": "special-order 6-cyl", "D": "273 V8 2-bbl",
           "E": "273 V8 4-bbl High Performance", "F": "318 V8 2-bbl", "G": "383 V8 2-bbl", "H": "383 V8 4-bbl",
           "J": "426 Hemi V8 2x4-bbl", "K": "440 V8 4-bbl", "L": "440 V8 4-bbl High Performance", "M": "special-order 8-cyl"},
    1968: _M_6869, 1969: _M_6869,
    1970: {**_M_7071, "J": "340 V8 3x2-bbl (1970 T/A, AAR)"},
    1971: {**_M_7071, "M": "400 V8 2-bbl"},
    1972: {"B": "198 L6 1-bbl", "C": "225 L6 1-bbl", "E": "special-order 6-cyl", "G": "318 V8 2-bbl",
           "H": "340 V8 4-bbl High Performance", "K": "360 V8 2-bbl", "M": "400 V8 2-bbl", "P": "400 V8 4-bbl High Performance",
           "T": "440 V8 4-bbl", "U": "440 V8 4-bbl High Performance", "V": "440 V8 3x2-bbl", "Z": "special-order 8-cyl"},
    1973: {"B": "198 L6 1-bbl", "C": "225 L6 1-bbl", "E": "special-order 6-cyl", "G": "318 V8 2-bbl",
           "H": "340 V8 4-bbl High Performance", "K": "360 V8 2-bbl", "M": "400 V8 2-bbl", "P": "400 V8 4-bbl High Performance",
           "T": "440 V8 4-bbl", "U": "440 V8 4-bbl High Performance", "Z": "special-order 8-cyl"},
    1974: {"B": "198 L6 1-bbl", "C": "225 L6 1-bbl", "E": "special-order 6-cyl", "G": "318 V8 2-bbl", "K": "360 V8 2-bbl",
           "L": "360 V8 4-bbl High Performance", "M": "400 V8 2-bbl", "P": "400 V8 4-bbl High Performance",
           "T": "440 V8 4-bbl", "U": "440 V8 4-bbl High Performance", "Z": "special-order 8-cyl"},
}
MOPAR_PLANTS = {"A": "Lynch Road, Detroit, MI", "B": "Hamtramck, MI", "C": "Jefferson Ave, Detroit, MI", "D": "Belvidere, IL",
                "E": "Los Angeles, CA", "F": "Newark, DE", "G": "St. Louis, MO", "H": "New Stanton, PA (1970-71 listing)",
                "R": "Windsor, ON, Canada"}
MOPAR_PLANTS_6667 = {"1": "Lynch Road, Detroit, MI", "2": "Hamtramck, MI", "3": "Jefferson Ave, Detroit, MI", "4": "Belvidere, IL",
                     "5": "Los Angeles, CA", "6": "Newark, DE", "7": "St. Louis, MO", "8": "Export", "9": "Windsor, ON, Canada"}
# Fender-tag engine sales codes (S19 mopar1.us 1969-71 codes; S20 e-bodies.org 1970; S21 stockmopar.com 1969-74 tag guide)
MOPAR_FENDER_ENGINE = {"E22": "198 6-cyl 1-bbl", "E24": "225 6-cyl 1-bbl", "E25": "225 6-cyl 1-bbl HD", "E31": "273 2-bbl",
                       "E44": "318 2-bbl", "E55": "340 4-bbl (340 3x2-bbl with A53 T/A/AAR pkg, 1970)", "E56": "340 3x2-bbl",
                       "E57": "360 2-bbl", "E61": "383 2-bbl", "E63": "383 4-bbl HP (1969-70) / 400 2-bbl (1971+)",
                       "E74": "426 Hemi", "E85": "440 4-bbl", "E86": "440 4-bbl HP", "E87": "440 3x2-bbl (Six Pack / Six Barrel)"}
# fender code -> [(first_year, last_year, allowed VIN 5th characters)]
MOPAR_E_TO_VIN = {
    "E22": [(1970, 1974, {"B"})], "E24": [(1969, 1969, {"B"}), (1970, 1974, {"C"})], "E25": [(1969, 1969, {"B"}), (1970, 1974, {"C"})],
    "E31": [(1968, 1969, {"D"})], "E44": [(1968, 1969, {"F"}), (1970, 1974, {"G"})],
    "E55": [(1968, 1969, {"P"}), (1970, 1970, {"H", "J"}), (1971, 1973, {"H"})], "E56": [(1970, 1970, {"J"})],
    "E57": [(1971, 1974, {"K"})], "E61": [(1968, 1969, {"G"}), (1970, 1971, {"L"})],
    "E63": [(1968, 1969, {"H"}), (1970, 1970, {"N"}), (1971, 1974, {"M", "N"})],
    "E74": [(1966, 1966, {"H"}), (1967, 1969, {"J"}), (1970, 1971, {"R"})],
    "E85": [(1967, 1969, {"K"}), (1970, 1974, {"T"})], "E86": [(1967, 1969, {"L", "M"}), (1970, 1974, {"U"})],
    "E87": [(1969, 1969, {"M"}), (1970, 1972, {"V"})],
}

# ----------------------------------------------------------------- model
@dataclass
class Field:
    value: str
    meaning: str
    source: str = ""

@dataclass
class Result:
    input: str
    family: str = "unknown"
    year: int | None = None
    year_candidates: list = field(default_factory=list)
    make: str | None = None
    model_series: str | None = None
    body_style: str | None = None
    engine: str | None = None
    plant: str | None = None
    sequence: str | None = None
    fields: dict = field(default_factory=dict)
    flags: list = field(default_factory=list)   # (severity, message)
    notes: list = field(default_factory=list)
    confidence: str = "low"
    confidence_score: float = 0.0
    tag: dict | None = None

    def flag(self, sev, msg): self.flags.append({"severity": sev, "message": msg})
    def to_dict(self): return asdict(self)

def _f(r, key, value, meaning, src):
    r.fields[key] = asdict(Field(value, meaning, src))

# ----------------------------------------------------------------- decoders
def _decade(digit: str, candidates: list[int], hint: int | None):
    c = [y for y in candidates if str(y)[-1] == digit]
    if hint and hint in c: return hint, c
    return (c[0] if len(c) == 1 else None), c

def decode_gm(vin, r, hint):
    div = GM_DIVISION.get(vin[0]); r.family = "GM 13-char (1965-80)"
    r.make = div; _f(r, "division", vin[0], div or "unknown division", "S1/S6")
    if not div: r.flag("error", f"Division '{vin[0]}' is not Chevrolet (1) or Pontiac (2): out of scope.")
    new = vin[1].isalpha()          # 1972+ series letter; 1965-71 numeric series
    yd = vin[5]
    if new:
        yrs = list(range(1972, 1980)) + [1980] if yd != "A" else [1980]
        year = 1980 if yd == "A" else None
        if yd != "A": year, yrs = _decade(yd, list(range(1972, 1980)), hint)
        r.year, r.year_candidates = year, yrs
        body = vin[2:4]; eng = vin[4]
        if div == "Chevrolet":
            r.model_series = CHEV_SERIES_7280.get(vin[1]); _f(r, "series", vin[1], r.model_series or "unknown", "S3")
            tbl = CHEV_ENGINE_1972 if year == 1972 else CHEV_ENGINE_7380
            r.engine = tbl.get(eng)
            _f(r, "engine", eng, r.engine or "unknown code", "S3/S4/S8")
            if not r.model_series: r.flag("error", f"Unknown Chevrolet series letter '{vin[1]}'.")
            if not r.engine: r.flag("warn", f"Engine code '{eng}' not in table for {year}.")
            r.plant = CHEV_PLANTS.get(vin[6])
        else:
            r.model_series = f"Pontiac series '{vin[1]}' (1972-80 series table not yet loaded)"
            r.engine = f"code '{eng}' (Pontiac 1972-80 engine table not yet loaded)"
            r.flag("warn", "Pontiac 1972-80 series/engine tables not implemented; structural decode only.")
            r.plant = PONT_PLANTS.get(vin[6])
        _f(r, "year", yd, str(year or yrs), "S3")
    else:
        if not vin[1:3].isdigit(): r.flag("error", "Positions 2-3 must be digits (1965-71) or a letter (1972+).")
        series = vin[1:3]; body = vin[3:5]
        year, yrs = _decade(yd, list(range(1965, 1972)), hint)
        if not yd.isdigit(): r.flag("error", f"Year digit '{yd}' invalid for 1965-71 GM format.")
        r.year, r.year_candidates = year, yrs
        _f(r, "year", yd, str(year), "S1/S5")
        if div == "Chevrolet":
            s = CHEV_SERIES_6571.get(series)
            r.model_series = s[0] if s else None
            if s: r.engine = ("V8 (displacement NOT encoded in 1965-71 Chevrolet VIN)" if s[1] == 8
                              else "6-cylinder (displacement not encoded)")
            r.plant = CHEV_PLANTS.get(vin[6]) if vin[6] != "H" or year == 1964 else CHEV_PLANTS["H"]
            if series in ("37", "38") and year and year >= 1969:
                r.notes.append("From 1969 the Chevelle SS 396 was an option package (RPO Z25), not a VIN series: "
                               "a 136xx VIN is consistent with a real SS but cannot prove it (S1, S2).")
            if series == "36" and year == 1969:
                r.notes.append("1969 SS 396 cars carry 136-series VINs (Malibu V8). Verify SS via build sheet, "
                               "cowl tag, engine suffix code and documentation.")
            if series in ("23", "24") and year and year < 1967: r.flag("error", "Camaro series code before 1967.")
        else:
            r.model_series = PONT_SERIES_6571.get(series)
            r.engine = "not encoded in 1965-71 Pontiac VIN (check engine block code)"
            r.plant = PONT_PLANTS.get(vin[6])
            if series == "42" and year == 1965: r.flag("warn", "1965 GTO was an option on LeMans (237xx); 242xx used from 1966 (S5).")
            if series in ("26", "28") and year and year < 1970: r.flag("warn", "Formula/Trans Am series codes are 1970-71.")
        _f(r, "series", series, r.model_series or "unknown", "S1/S2/S5")
        if not r.model_series: r.flag("error", f"Unknown series code '{series}' for {div}.")
    r.body_style = GM_BODY.get(body); _f(r, "body", body, r.body_style or "unknown", "S1/S6")
    if not r.body_style: r.flag("error", f"Unknown body style code '{body}'.")
    _f(r, "plant", vin[6], r.plant or "unknown", "S1/S5")
    if not r.plant: r.flag("error", f"Unknown assembly plant '{vin[6]}'.")
    r.sequence = vin[7:]; _f(r, "sequence", r.sequence, "plant sequential production number", "S1")
    if not r.sequence.isdigit(): r.flag("error", "Sequence (positions 8-13) must be 6 digits.")
    if r.year == 1969 and "Chevelle" in (r.model_series or "") and r.sequence.isdigit() and vin[6] != "1" and int(r.sequence) < 300001:
        r.flag("warn", "1969 US-built Chevelle sequences began at 300001 (S1); this number is below that.")

def decode_ford(vin, r, hint):
    r.family = "Ford/Mercury 11-char (1965-79)"
    yd = vin[0]; year, yrs = _decade(yd, list(range(1965, 1980)), hint)
    if not year and len(yrs) > 1:   # narrow decade using body/engine code validity windows
        b0 = FORD_BODY.get(vin[2:4]); e0 = FORD_ENGINE.get(vin[4], [])
        narrowed = [y for y in yrs if (not b0 or any(w[0] <= y <= w[1] for w in b0)) and any(a <= y <= z for a, z, _ in e0)]
        if len(narrowed) == 1:
            year = narrowed[0]; r.notes.append(f"Decade resolved to {year} from body/engine code validity.")
    r.year, r.year_candidates = year, yrs
    if not year and len(yrs) > 1: r.flag("warn", f"Year digit '{yd}' is ambiguous ({yrs}); pass --year to resolve.")
    _f(r, "year", yd, str(year or yrs), "S9")
    r.plant = FORD_PLANTS.get(vin[1]); _f(r, "plant", vin[1], r.plant or "unknown", "S10/S11")
    if not r.plant: r.flag("error", f"Unknown Ford plant '{vin[1]}'.")
    body = vin[2:4]; wins = FORD_BODY.get(body, [])
    y = year or (yrs[0] if yrs else None)
    txt, bsrc = ford_body(body, y)
    if txt:
        r.body_style = txt
        r.model_series = re.split(r" (?:2-door|4-door|convertible|fastback)", txt)[0]
        r.make = "Mercury" if "Mercury" in txt else "Ford"
    elif wins:
        r.make = "Ford/Mercury"; r.model_series = f"body serial {body}"
        spans = ", ".join(f"{a}-{z} {t}" for a, z, t, _ in wins)
        r.flag("error", f"Body code {body} not used in {y} (known uses: {spans}).")
    else:
        r.make = "Ford/Mercury"; r.model_series = f"body serial {body} (not in loaded tables)"
        r.flag("warn", f"Body serial '{body}' not in loaded tables (Mustang/Cougar, 1968-71 Fairlane/Torino, 1968 full-size Ford).")
    _f(r, "body", body, r.body_style or "unknown", bsrc or "S9/S16/S17")
    eng = vin[4]; m = None
    for a, z, txt in FORD_ENGINE.get(eng, []):
        if y and a <= y <= z: m = txt
    r.engine = m; _f(r, "engine", eng, m or "unknown for this year", "S9/S11")
    if not m: r.flag("warn", f"Engine code '{eng}' not documented for {y} in loaded table.")
    r.sequence = vin[5:]; _f(r, "sequence", r.sequence, "consecutive unit number", "S9")
    if not r.sequence.isdigit(): r.flag("error", "Unit number (positions 6-11) must be digits.")
    if body in ("45", "46") and y == 1969 or (body == "38" and y in (1970, 1971)):
        r.notes.append("Cobra body serial: high-value configuration; confirm engine code and Marti Report before valuing.")
    if vin[1] == "S" and body in ("09",) and y in (1965, 1966):
        r.notes.append("Plant S (Allen Park) is associated with 1965-66 Shelby GT350 provenance; verify with SAAC registry.")

def decode_mopar(vin, r, hint):
    early = vin[6].isdigit()            # 1966-67 use a numeric plant code; 1968+ use a letter (S18)
    r.family = "Chrysler 13-char (1966-67 tables)" if early else "Chrysler 13-char (1968-74 tables)"
    r.make = {"B": "Plymouth", "R": "Plymouth", "V": "Plymouth", "P": "Plymouth", "C": "Chrysler", "Y": "Imperial"}.get(
        vin[0], "Dodge" if vin[0] in "LWXJD" else None)
    yd = vin[5]
    year, yrs = _decade(yd, [1966, 1967] if early else list(range(1968, 1975)), hint)
    r.year, r.year_candidates = year, yrs
    if not yrs: r.flag("error", f"Year digit '{yd}' not valid for a {'1966-67' if early else '1968-74'} Chrysler VIN (plant code '{vin[6]}').")
    elif not year and len(yrs) > 1: r.flag("warn", f"Year digit '{yd}' ambiguous ({yrs}); pass --year.")
    _f(r, "year", yd, str(year or yrs), "S18")
    line = MOPAR_LINE.get(vin[0]); cls = MOPAR_CLASS.get(vin[1])
    name = MOPAR_MODELNAME.get(vin[:2]) if year == 1969 else None
    r.model_series = f"{name or line} ({cls} price class)" if (line and cls) else None
    _f(r, "car_line", vin[0], line or "unknown", "S12/S18"); _f(r, "price_class", vin[1], cls or "unknown", "S12/S15/S18")
    if not line: r.flag("error", f"Unknown car line '{vin[0]}'.")
    if not cls: r.flag("error", f"Unknown price class '{vin[1]}'.")
    if vin[0] == "J" and year and year < 1970: r.flag("error", "Challenger (J) did not exist before 1970.")
    if vin[0] == "X" and year and year > 1970: r.flag("error", "Car line X (Charger) not used after 1970; 1971+ Chargers are W.")
    if vin[1] == "O" and year and year > 1967: r.flag("warn", "Price class O (Super Stock) is listed only for 1966-67.")
    r.body_style = MOPAR_BODY.get(vin[2:4]); _f(r, "body", vin[2:4], r.body_style or "unknown", "S12/S18")
    if not r.body_style: r.flag("error", f"Unknown body code '{vin[2:4]}'.")
    y = year or (yrs[0] if yrs else None); eng = vin[4]
    tbl = MOPAR_ENGINE.get(y, {})
    r.engine = tbl.get(eng); _f(r, "engine", eng, r.engine or "unknown / table not loaded", "S18/S12")
    if not tbl: r.flag("warn", f"Mopar engine table for {y} not loaded; engine code shown raw.")
    elif not r.engine: r.flag("error", f"Engine code '{eng}' not valid for {y}.")
    plants = MOPAR_PLANTS_6667 if early else MOPAR_PLANTS
    r.plant = plants.get(vin[6]); _f(r, "plant", vin[6], r.plant or "unknown", "S18")
    if not r.plant: r.flag("error", f"Unknown Chrysler plant '{vin[6]}'.")
    r.sequence = vin[7:]; _f(r, "sequence", r.sequence, "sequence (serial) number", "S18")
    if not r.sequence.isdigit(): r.flag("error", "Sequence must be 6 digits.")
    if r.engine and "Hemi" in r.engine:
        r.notes.append("Hemi engine code: high-value, high-fraud configuration. Human review required.")

# ----------------------------------------------------------------- tags
def decode_tag(tag: str, r: Result):
    """Very small trim/cowl/fender tag parser used to cross-check the VIN."""
    t = tag.upper(); out = {"raw": tag, "checks": []}
    m = re.search(r"\bST\s*(\d{2})-(\d)(\d{2})(\d{2})", t)      # GM Fisher Body cowl tag, e.g. ST 69-13637
    if m:
        yy, div, ser, body = m.groups()
        out.update(kind="GM cowl tag", year=1900 + int(yy), division=div, series=ser, body=body)
        if r.year and 1900 + int(yy) != r.year: r.flag("error", f"Cowl tag year 19{yy} != VIN year {r.year}.")
        if r.input[:1] != div: r.flag("error", "Cowl tag division digit does not match VIN.")
        # tag series digit 3 is not V8/6 specific (S2): compare first two only
        if r.input[1:3].isdigit() and r.input[1] != ser[0]: r.flag("error", f"Cowl tag series {div}{ser} conflicts with VIN.")
        if r.input[3:5].isdigit() and r.input[3:5] != body: r.flag("error", f"Cowl tag body {body} != VIN body {r.input[3:5]}.")
        out["checks"].append("year/division/series/body compared with VIN")
    for code, txt in MOPAR_FENDER_ENGINE.items():  # Mopar fender tag engine sales code
        if re.search(rf"\b{code}\b", t):
            out.setdefault("kind", "Mopar fender tag"); out["engine_sales_code"] = f"{code} = {txt}"
            if r.family.startswith("Chrysler"):
                y = r.year or (r.year_candidates[0] if r.year_candidates else None)
                ok = [w[2] for w in MOPAR_E_TO_VIN.get(code, []) if y and w[0] <= y <= w[1]]
                if not ok:
                    r.flag("warn", f"Fender tag {code} has no VIN cross-reference loaded for {y}.")
                elif r.input[4] not in set().union(*ok):
                    r.flag("error", f"Fender tag {code} ({txt}) conflicts with VIN engine code '{r.input[4]}' for {y}.")
    m = re.search(r"\b(\d[A-Z]\d{2}[A-Z]\d{6})\b", t)                 # Ford door data plate VIN line
    if m:
        out.setdefault("kind", "Ford door data plate"); out["plate_vin"] = m.group(1)
        if m.group(1) != r.input: r.flag("error", f"Door plate VIN {m.group(1)} != VIN {r.input}.")
    out.setdefault("kind", "unrecognised"); r.tag = out
    if out["kind"] == "unrecognised": r.flag("warn", "Tag text not recognised; no cross-check performed.")

# ----------------------------------------------------------------- entry
def decode(vin: str, year_hint: int | None = None, tag: str | None = None) -> Result:
    raw = vin; vin = re.sub(r"[\s\-]", "", vin.upper()); r = Result(input=vin)
    if vin != raw.upper().strip(): r.notes.append("Spaces/dashes removed from input.")
    if not re.fullmatch(r"[A-Z0-9]+", vin or "-"): r.flag("error", "VIN contains illegal characters."); return _score(r)
    if len(vin) == 17: r.flag("error", "17-character VIN = 1981 or later; outside 1964-80 scope."); return _score(r)
    if len(vin) == 11 and vin[0].isdigit() and vin[1].isalpha(): decode_ford(vin, r, year_hint)
    elif len(vin) == 13 and vin[0] in "12": decode_gm(vin, r, year_hint)
    elif len(vin) == 13 and vin[0].isalpha(): decode_mopar(vin, r, year_hint)
    elif len(vin) == 12 and vin[0] == "4":
        r.family = "Chevrolet 1964 12-char (structure only)"; r.year = 1964; r.make = "Chevrolet"
        r.plant = CHEV_PLANTS.get(vin[5]); r.sequence = vin[6:]
        r.flag("warn", "1964 Chevrolet format decoded structurally only.")
    else:
        r.flag("error", f"Length {len(vin)} / pattern does not match any supported 1964-80 GM, Ford or Mopar format.")
    if year_hint and r.year and year_hint != r.year: r.flag("error", f"Claimed year {year_hint} != VIN year {r.year}.")
    if year_hint and r.year_candidates and year_hint not in r.year_candidates:
        r.flag("error", f"Claimed year {year_hint} impossible for this VIN (candidates {r.year_candidates}).")
    if r.year and not (1964 <= r.year <= 1980): r.flag("error", "Year outside 1964-80 scope.")
    if tag: decode_tag(tag, r)
    return _score(r)

def _score(r: Result) -> Result:
    keys = [r.year, r.make, r.model_series, r.body_style, r.engine, r.plant, r.sequence]
    s = sum(1 for k in keys if k) / len(keys)
    errs = sum(f["severity"] == "error" for f in r.flags); warns = sum(f["severity"] == "warn" for f in r.flags)
    s = max(0.0, s - 0.35 * errs - 0.1 * warns)
    if r.tag and r.tag.get("kind") != "unrecognised" and errs == 0: s = min(1.0, s + 0.05)
    r.confidence_score = round(s, 2)
    r.confidence = "high" if s >= 0.85 and errs == 0 else "medium" if s >= 0.55 and errs == 0 else "low"
    return r

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(); p.add_argument("vin"); p.add_argument("--year", type=int); p.add_argument("--tag")
    a = p.parse_args(); print(json.dumps(decode(a.vin, a.year, a.tag).to_dict(), indent=2))
