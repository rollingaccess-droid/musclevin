import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from decoder import decode

def errs(r): return [f for f in r.flags if f["severity"] == "error"]

def test_1969_chevelle_chevellestuff_example():           # S2: 136379A307416
    r = decode("136379A307416")
    assert (r.year, r.make, r.body_style) == (1969, "Chevrolet", "2-door sport coupe (hardtop)")
    assert "Malibu" in r.model_series and r.plant.startswith("Atlanta") and r.sequence == "307416"
    assert r.engine.startswith("V8") and r.confidence == "high" and not errs(r)

def test_1969_chevelle_convertible_baltimore():           # S1: 136679B410561
    r = decode("136679B410561"); assert r.body_style == "2-door convertible" and r.plant.startswith("Baltimore")

def test_1969_gto_forum_vin():                            # S7: 242379R157868
    r = decode("242379R157868")
    assert r.make == "Pontiac" and r.model_series.startswith("GTO") and r.plant == "Arlington, TX" and r.year == 1969

def test_1969_road_runner_classicvindecoder():            # S13: RM23H9G170193
    r = decode("RM23H9G170193")
    assert r.make == "Plymouth" and "Road Runner" in r.model_series and "383" in r.engine and r.plant == "St. Louis, MO"

def test_1969_charger_rt_jegs_example():                  # S14: XS29L9B123456
    r = decode("XS29L9B123456")
    assert "Charger R/T" in r.model_series and "440" in r.engine and r.plant == "Hamtramck, MI"

def test_mustang_mustangnerd_example():                   # S9: 7F02C123456
    r = decode("7F02C123456", year_hint=1967)
    assert r.year == 1967 and r.plant == "Dearborn, MI" and "fastback" in r.body_style and "289" in r.engine

def test_1973_camaro_example():                           # S8: 1Q87L2L100000 (year digit 2 = 1972)
    r = decode("1Q87L2L100000"); assert r.year == 1972 and "Camaro" in r.model_series and "350" in r.engine

def test_ford_year_ambiguity_flagged():
    r = decode("9F02R123456"); assert r.year == 1969   # R=428CJ only 1968-70 -> 1969
    r = decode("6F07Z123456"); assert r.year is None and r.confidence != "high"

def test_invalid_inputs():
    assert errs(decode("1G1YY22G965104378"))            # modern 17-char
    assert errs(decode("13637"))                        # too short
    assert errs(decode("136379Q307416"))                # bad plant
    assert errs(decode("JS23R9B100001"))                # Challenger in 1969

def test_cowl_tag_cross_check():
    ok = decode("136379A307416", tag="ST 69-13637 ATL 123456 BDY")
    bad = decode("136379A307416", tag="ST 69-13667 ATL 123456 BDY")
    assert not errs(ok) and errs(bad) and bad.confidence == "low"

def test_claimed_year_mismatch():
    assert errs(decode("136379A307416", year_hint=1970))

def test_fender_tag_engine_conflict():
    assert errs(decode("RM23H9G170193", tag="E74 D32 ..."))

# ---- Ford intermediates / full-size (S16 ford-torino.de, S17 mercurystuff.com, coyoteclassics example)
def test_1969_torino_gt_convertible_fordtorino_example():  # S16: 9H43F206211
    r = decode("9H43F206211", year_hint=1969)
    assert r.body_style == "Torino GT 2-door convertible" and r.plant.startswith("Lorain") and "302" in r.engine and not errs(r)

def test_1970_torino_cobra_fordtorino_example():           # S16: 0A38N223512
    r = decode("0A38N223512", year_hint=1970)
    assert "Torino Cobra" in r.body_style and "429" in r.engine and r.make == "Ford" and not errs(r)
    assert any("Cobra" in n for n in r.notes)

def test_1971_torino_gt_fordtorino_example():              # S16: 1A35H129342
    r = decode("1A35H129342", year_hint=1971)
    assert r.body_style.startswith("Torino GT") and "351" in r.engine and not errs(r)

def test_1968_vs_1969_body_code_differs():
    assert "Fairlane 500" in decode("8A35F100001", year_hint=1968).body_style
    assert "Torino GT" in decode("0A35F100001", year_hint=1970).body_style

def test_cobra_code_rejected_in_1968():
    assert errs(decode("8A46R100001", year_hint=1968))

def test_1968_galaxie_xl_example():                        # coyoteclassics.com: 8P60Z170704 (S17 body table)
    r = decode("8P60Z170704", year_hint=1968)
    assert r.body_style.startswith("Galaxie 500 XL") and r.plant.startswith("Twin Cities") and not errs(r)

# ---- Mopar engine-letter corrections (S18/S12)
def test_mopar_1970_C_is_225_and_B_is_198():
    assert "225" in decode("VL41C0B100001").engine and "198" in decode("VL41B0B100001").engine

def test_mopar_1971_M_is_400_and_J_invalid():
    assert "400" in decode("WL41M1A100001").engine
    assert errs(decode("JS23J1B100001"))                 # 340 Six Pack J code was 1970 only

def test_mopar_1972_74_tables_loaded():
    assert "400" in decode("RM23P2A100001").engine
    r = decode("VS29L4B100001"); assert "360" in r.engine and "4-bbl" in r.engine
    assert errs(decode("RM23R2A100001"))                 # no Hemi after 1971

def test_mopar_1971_charger_uses_W_not_X():
    assert errs(decode("XS29R1B100001"))

# ---- Mopar 1966-67 (S18); VINs are synthetic, built to the published layout
def test_mopar_1966_hemi_numeric_plant():
    r = decode("RS23H67100001")
    assert r.year == 1966 and "Hemi" in r.engine and r.plant == "St. Louis, MO" and r.make == "Plymouth" and not errs(r)

def test_mopar_1967_gtx_440():
    r = decode("RS23L77100001")
    assert r.year == 1967 and "440" in r.engine and "High Performance" in r.engine and not errs(r)

def test_mopar_1967_bad_engine_and_year():
    assert errs(decode("WS23V72100001"))                 # V not used in 1967
    assert errs(decode("WS23L92100001"))                 # numeric plant + year 9 is inconsistent

# ---- Fender tag year-aware cross-checks (S19/S20/S21)
def test_fender_tag_year_aware():
    assert errs(decode("RM23J9G100001", tag="E74")) == []        # 1969 Hemi = J
    assert errs(decode("RM23R9G100001", tag="E74"))              # R is not a 1969 engine letter / not Hemi
    assert errs(decode("RM23R0G100001", tag="E74")) == []        # 1970 Hemi = R
    assert errs(decode("RM23J0G100001", tag="E74"))              # 1970 J is 340 Six Pack, not Hemi
    assert errs(decode("BS23J0B294098", tag="E55 D32")) == []    # 1970 AAR/T-A: E55 + VIN J (S20 example)
    assert errs(decode("RM23N0G100001", tag="E61"))              # E61 = 383 2-bbl -> L in 1970
