# Classic muscle-car VIN and trim tag decoder (phase-1 prototype)

Uses only the Python standard library. Covers 1964-1980 Chevrolet, Pontiac, Ford/Mercury, Dodge and Plymouth.
Each decoded field records the source ID (S1..S15) its rule came from.

```bash
python3 decoder.py 136379A307416 --year 1969 --tag "ST 69-13637 ATL BDY"   # JSON output
../.venv/bin/python -m pytest -q tests                                     # 26 tests
../.venv/bin/python make_report.py ../sample-report.pdf                    # needs reportlab (in ../.venv)
```

The decoder returns year (plus any decade candidates), make, model/series, body style, engine meaning, assembly plant, sequence number,
per-position fields with sources, error/warn flags, notes, and a confidence level (high/medium/low) with a score.
Any error forces confidence to low.

## Coverage matrix
| Family | Years | Status |
|---|---|---|
| Chevrolet 13-char (numeric series) | 1965-71 | Chevelle, Camaro, Chevy II/Nova and Corvette series. Body, plant, sequence. The engine field gives only V8 vs 6-cyl, because displacement is not in the VIN. 1969 Chevelle sequence sanity check |
| Chevrolet 13-char (letter series + engine) | 1972-80 | Series, body, engine table (1972 table and a generic 1973-80 table), plant |
| Pontiac 13-char | 1965-71 | GTO, Tempest/LeMans, Firebird/Formula/Trans Am and Catalina series, plant. The VIN has no engine code |
| Pontiac | 1972-80 | **Structure only.** Series and engine tables not loaded |
| Ford/Mercury 11-char | 1965-79 | Plant, year (the decade is resolved from body and engine validity windows, otherwise flagged), year-windowed body codes for Mustang/Cougar (S9), 1968-71 Fairlane/Torino/Ranchero (S16) and 1968 full-size Custom/Galaxie/XL/LTD (S17), year-windowed engine codes for the 1965-73 muscle era (1970-71 429 codes from S16). A body code used outside its known years is an error |
| Dodge/Plymouth 13-char | 1966-74 | Car line, price class, model name (1969 two-letter table), body, plant (numeric 1-9 for 1966-67, letters 1968+), per-year engine tables 1966-74 (S18, cross-checked with S12/S19 for 1969-71) |
| Chevrolet 12-char | 1964 | Structure only |
| Mopar 1964-65, Pontiac 1964, AMC, Olds, Buick | - | Not supported. Returns an error or low confidence |

Tag cross-checks: GM Fisher Body cowl tag `ST yy-dsssbb` (year, division, series, body), Mopar fender tag engine sales codes
(E22-E87, S19-S21) against the VIN engine letter, using year windows (e.g. E74 must be H in 1966, J in 1967-69, R in 1970-71), and the Ford door data plate VIN line against the VIN.

## Known limitations
* The tables are partial and hand-entered from secondary enthusiast sources, not factory manuals. A person must review them before production.
* Engine letters were reused across years (Ford, Mopar, and Chevy 1973-80 have model-specific exceptions). Treat engine meanings as "per public chart".
* The year digit repeats every decade: Ford 6 = 1966 or 1976, Mopar 0 = 1970 or 1980. Without `--year`, the decoder narrows the year only where the code tables allow it.
* A VIN cannot prove a performance package where it was an option: 1969-72 Chevelle SS, 1965 GTO, Road Runner/Hemi "clones". The decoder adds notes for these cases.
* The decoder checks structure and internal consistency only. It cannot detect a re-stamped or swapped VIN plate, or a forged tag.
* The confidence score is a simple heuristic (field coverage minus penalties for errors and warnings). It is not calibrated.
* The sample PDF uses an example VIN published on chevellestuff.net. The cowl tag text is a synthetic sample.

## Sources (accessed 2026-10-15)
* S1 chevellestuff.net 1969 Chevelle VINs: https://chevellestuff.net/1969/vin.htm (VIN 136679B410561 example; plant table; 300001 sequence start)
* S2 chevellestuff.net Protect-O-Plate VIN: https://chevellestuff.net/1969/pop/pop_vin.htm (VIN 136379A307416; odd/even 3rd digit = 6/V8)
* S2b ChevelleWorld 1969 VIN charts: http://macswebs.com/chevelleworld/decode/vin/chevelle_69_vin_charts.html and plant/sequence table http://macswebs.com/chevelleworld/misc/plant_designations.htm
* S3 Ground Up SS396 pre-1981 GM VIN guide: https://www.ss396.com/cars/decode-chevrolet-vin-code/
* S4 1972 Chevrolet VIN charts: http://macswebs.com/qdtech/misc/72_chevrolet_vin_charts.htm
* S5 Tin Indian Performance GTO VIN decoding: https://tinindianperformance.com/Pontiac%20GTO%20VIN%20decoding.htm
* S6 carcheckervin classic GM decoder: https://www.carcheckervin.com/classic-gm-vin-decoder ; Pontiac VIN decoder PDF: https://www.rubbertherightway.com/file/20-Pontiac+VIN+Decoder+1965-2002.pdf
* S7 GTO Forum, VIN 242379R157868: https://www.gtoforum.com/threads/69-gto-vin-242379-r-157868-judge.54753/
* S8 Camaro VIN decode (1Q87L2L100000 example and engine codes): https://www.chevy-camaro.com/chevy-camaro-VIN-decode-all.php ; Nova: https://paddockparts.com/wp-content/uploads/2012/03/Nova_VINDecoding.pdf
* S9 Mustang Nerd VIN decoder (7F02C123456 example; body and plant tables): https://mustangnerd.com/technical-tools/mustang-vin-decoder
* S10 TPOCR 1970 Ford VIN plants: https://www.tpocr.com/fordvin10.html ; Ford plant list: https://vinvaquero.com/ford/
* S11 carcheckervin classic Ford decoder: https://www.carcheckervin.com/classic-ford-vin-decoder
* S12 440 Magnum Network 1969 Mopar VIN breakdown: https://www.440magnum-network.com/mopar-information/vin-code-breakdowns/1969-vins/ ; lhmopars 1966-74 (search snippet; direct fetch returned 403): https://www.lhmopars.net/vin66-74.htm
* S13 Classic VIN Decoder result, RM23H9G170193: https://www.classicvindecoder.com/results/RM23H9G170193
* S14 JEGS Mopar VIN guide (XS29L9B123456 example; 1970s engine codes): https://www.jegs.com/tech-articles/decoding-mopar-vin-numbers-a-complete-guide-for-cars-and-trucks-from-1946-to-today/
* S15 Ultimate Muscle Car 1969 Mopar decoder (car line + price class names): https://ultimatemusclecar.com/1969-mopar-vin-decoder/

* S16 Ford-Torino.de VIN decoder, model years 1968-71 (body serial and engine codes; examples 8A40F275281, 9H43F206211, 0A38N223512, 1A35H129342): https://www.ford-torino.de/en/facts-figures/vin-decoder/model-year-1969/ (and /model-year-1968/, /model-year-1970/, /model-year-1971/); Hagerty Torino GT buyer's guide cross-check: https://www.hagerty.com/media/buying-and-selling/ford-torino-gt-buyers-guide/
* S17 MercuryStuff 1968 Ford & Mercury identification (full-size body serial codes 50-76): https://www.mercurystuff.com/1968-ford-mercury-vehicle-identification.html ; example 8P60Z170704 (1968 Galaxie XL): https://www.coyoteclassics.com/vehicles/894/1968-ford-galaxie-xl
* S18 Lee Herman 1966-74 Chrysler VIN tables (mirror): https://degeneratepress.com/newport/vin66-74.htm ; 1970/1971 cross-checks: https://www.440magnum-network.com/mopar-information/vin-code-breakdowns/1970-vins/ , https://www.stockmopar.com/mopar-vin-decoding.html
* S19 mopar1.us 1969-71 fender tag codes: https://www.mopar1.us/6971codes.html
* S20 E-Bodies 1970 fender tag codes (E55 + A53 = 340 Six Pack; example BS23J0B294098): https://www.e-bodies.org/mopar-fender-tag-decoder-build-sheet-vin/1970-mopar-cuda-challenger-options-fender-tag-codes/
* S21 StockMopar 1969-74 fender tag guide: https://stockmopar.com/how-to-decode-a-1969-1974-fender-tag-part-1.html

## Verification log (2026-10-15)
Fixed against S18/S12/S19-S21:
* 1970-71 engine table was missing B (198), E (special 6), K (360), Z (special V8); J (340 3x2) is now 1970 only; M = 400 2-bbl added for 1971.
* 1972-74 engine tables were missing entirely (warned on every car); now loaded. No R (Hemi) after 1971; 1974 L = 360 4-bbl.
* Fender tag cross-check was not year-aware (E74 accepted J or R in any year; E55 rejected 1970 T/A/AAR J-code cars). Now per-year; added E22/E24/E25/E31/E44/E56/E57/E61/E85.
* E63 means 383 4-bbl HP in 1968-70 but 400 2-bbl from 1971/72 (S19 says 1971, S21 says 1972+); both readings are accepted for 1971.
* Car line Y (Imperial) added; X (Charger) flagged after 1970; plant H (New Stanton, 1970-71 listing) added; price classes O (1966-67) and G (1972+) added.
Still unverified (secondary sources only): 1969 M-code / E87 mapping for the 1969-1/2 440 six-barrel cars; 1966-67 fender tags (no E-code cross-check loaded); 1968 Ford Z engine code; full-size Ford body codes after 1968. 1966-67 Mopar tests use synthetic VINs built to the S18 layout.
