// Faithful port of app/decoder.py. The Python module is the source of truth.
// Tables live in decoder-data.js and are generated from that module.
import { TABLES } from "./decoder-data.js";

function get(obj, key, fallback = null) {
  if (obj != null && Object.prototype.hasOwnProperty.call(obj, key)) return obj[key];
  return fallback;
}

function range(start, stop) {
  const out = [];
  for (let i = start; i < stop; i++) out.push(i);
  return out;
}

function isDigits(s) {
  return /^[0-9]+$/.test(s);
}

function isAlpha(s) {
  return /^[A-Za-z]+$/.test(s);
}

// Python truthiness: empty containers are false. JS arrays and objects are not.
function pyBool(v) {
  if (v == null || v === false) return false;
  if (typeof v === "number") return v !== 0 && !Number.isNaN(v);
  if (typeof v === "string") return v.length > 0;
  if (Array.isArray(v)) return v.length > 0;
  if (typeof v === "object") return Object.keys(v).length > 0;
  return Boolean(v);
}

// str(None) / str([1, 2]) as Python formats them inside messages and field meanings.
function pyInterp(v) {
  if (v == null) return "None";
  if (Array.isArray(v)) return "[" + v.join(", ") + "]";
  return String(v);
}

function roundHalfEven(num, places) {
  const sign = num < 0 ? -1 : 1;
  const shifted = Math.abs(num) * 10 ** places;
  const floor = Math.floor(shifted);
  let diff = shifted - floor;
  if (Math.abs(diff - 0.5) < 1e-8) diff = 0.5;
  if (diff < 1e-8) diff = 0;
  let rounded;
  if (diff > 0.5) rounded = floor + 1;
  else if (diff < 0.5) rounded = floor;
  else rounded = floor % 2 === 0 ? floor : floor + 1;
  return (sign * rounded) / 10 ** places;
}

function makeResult(input) {
  return {
    input,
    family: "unknown",
    year: null,
    year_candidates: [],
    make: null,
    model_series: null,
    body_style: null,
    engine: null,
    plant: null,
    sequence: null,
    fields: {},
    flags: [],
    notes: [],
    confidence: "low",
    confidence_score: 0,
    tag: null,
  };
}

function flag(r, sev, msg) {
  r.flags.push({ severity: sev, message: msg });
}

function addField(r, key, value, meaning, source) {
  r.fields[key] = { value, meaning, source };
}

function decade(digit, candidates, hint) {
  const c = candidates.filter((y) => String(y).slice(-1) === digit);
  if (hint && c.includes(hint)) return [hint, c];
  return [c.length === 1 ? c[0] : null, c];
}

function decodeGm(vin, r, hint) {
  const div = get(TABLES.GM_DIVISION, vin[0]);
  r.family = "GM 13-char (1965-80)";
  r.make = div;
  addField(r, "division", vin[0], div || "unknown division", "S1/S6");
  if (!div) flag(r, "error", `Division '${vin[0]}' is not Chevrolet (1) or Pontiac (2): out of scope.`);
  const isNew = isAlpha(vin[1]);
  const yd = vin[5];
  let body;
  let year;
  let yrs;
  if (isNew) {
    if (yd !== "A") {
      [year, yrs] = decade(yd, range(1972, 1980), hint);
    } else {
      yrs = [1980];
      year = 1980;
    }
    r.year = year;
    r.year_candidates = yrs;
    body = vin.slice(2, 4);
    const eng = vin[4];
    if (div === "Chevrolet") {
      r.model_series = get(TABLES.CHEV_SERIES_7280, vin[1]);
      addField(r, "series", vin[1], r.model_series || "unknown", "S3");
      const tbl = year === 1972 ? TABLES.CHEV_ENGINE_1972 : TABLES.CHEV_ENGINE_7380;
      r.engine = get(tbl, eng);
      addField(r, "engine", eng, r.engine || "unknown code", "S3/S4/S8");
      if (!r.model_series) flag(r, "error", `Unknown Chevrolet series letter '${vin[1]}'.`);
      if (!r.engine) flag(r, "warn", `Engine code '${eng}' not in table for ${pyInterp(year)}.`);
      r.plant = get(TABLES.CHEV_PLANTS, vin[6]);
    } else {
      r.model_series = `Pontiac series '${vin[1]}' (1972-80 series table not yet loaded)`;
      r.engine = `code '${eng}' (Pontiac 1972-80 engine table not yet loaded)`;
      flag(r, "warn", "Pontiac 1972-80 series/engine tables not implemented; structural decode only.");
      r.plant = get(TABLES.PONT_PLANTS, vin[6]);
    }
    addField(r, "year", yd, pyInterp(year || yrs), "S3");
  } else {
    if (!isDigits(vin.slice(1, 3))) flag(r, "error", "Positions 2-3 must be digits (1965-71) or a letter (1972+).");
    const series = vin.slice(1, 3);
    body = vin.slice(3, 5);
    [year, yrs] = decade(yd, range(1965, 1972), hint);
    if (!isDigits(yd)) flag(r, "error", `Year digit '${yd}' invalid for 1965-71 GM format.`);
    r.year = year;
    r.year_candidates = yrs;
    addField(r, "year", yd, pyInterp(year), "S1/S5");
    if (div === "Chevrolet") {
      const s = get(TABLES.CHEV_SERIES_6571, series);
      r.model_series = s ? s[0] : null;
      if (s) {
        r.engine = s[1] === 8
          ? "V8 (displacement NOT encoded in 1965-71 Chevrolet VIN)"
          : "6-cylinder (displacement not encoded)";
      }
      r.plant = vin[6] !== "H" || year === 1964 ? get(TABLES.CHEV_PLANTS, vin[6]) : TABLES.CHEV_PLANTS.H;
      if ((series === "37" || series === "38") && year && year >= 1969) {
        r.notes.push(
          "From 1969 the Chevelle SS 396 was an option package (RPO Z25), not a VIN series: " +
          "a 136xx VIN is consistent with a real SS but cannot prove it (S1, S2)."
        );
      }
      if (series === "36" && year === 1969) {
        r.notes.push(
          "1969 SS 396 cars carry 136-series VINs (Malibu V8). Verify SS via build sheet, " +
          "cowl tag, engine suffix code and documentation."
        );
      }
      if ((series === "23" || series === "24") && year && year < 1967) flag(r, "error", "Camaro series code before 1967.");
    } else {
      r.model_series = get(TABLES.PONT_SERIES_6571, series);
      r.engine = "not encoded in 1965-71 Pontiac VIN (check engine block code)";
      r.plant = get(TABLES.PONT_PLANTS, vin[6]);
      if (series === "42" && year === 1965) flag(r, "warn", "1965 GTO was an option on LeMans (237xx); 242xx used from 1966 (S5).");
      if ((series === "26" || series === "28") && year && year < 1970) flag(r, "warn", "Formula/Trans Am series codes are 1970-71.");
    }
    addField(r, "series", series, r.model_series || "unknown", "S1/S2/S5");
    if (!r.model_series) flag(r, "error", `Unknown series code '${series}' for ${pyInterp(div)}.`);
  }
  r.body_style = get(TABLES.GM_BODY, body);
  addField(r, "body", body, r.body_style || "unknown", "S1/S6");
  if (!r.body_style) flag(r, "error", `Unknown body style code '${body}'.`);
  addField(r, "plant", vin[6], r.plant || "unknown", "S1/S5");
  if (!r.plant) flag(r, "error", `Unknown assembly plant '${vin[6]}'.`);
  r.sequence = vin.slice(7);
  addField(r, "sequence", r.sequence, "plant sequential production number", "S1");
  if (!isDigits(r.sequence)) flag(r, "error", "Sequence (positions 8-13) must be 6 digits.");
  if (
    r.year === 1969 &&
    (r.model_series || "").includes("Chevelle") &&
    isDigits(r.sequence) &&
    vin[6] !== "1" &&
    Number(r.sequence) < 300001
  ) {
    flag(r, "warn", "1969 US-built Chevelle sequences began at 300001 (S1); this number is below that.");
  }
}

function fordBody(code, y) {
  for (const [a, z, txt, src] of TABLES.FORD_BODY[code] || []) {
    if (y && a <= y && y <= z) return [txt, src];
  }
  return [null, null];
}

function fordSeriesName(txt) {
  const m = txt.match(/ (?:2-door|4-door|convertible|fastback)/);
  return m ? txt.slice(0, m.index) : txt;
}

function decodeFord(vin, r, hint) {
  r.family = "Ford/Mercury 11-char (1965-79)";
  const yd = vin[0];
  let [year, yrs] = decade(yd, range(1965, 1980), hint);
  if (!year && yrs.length > 1) {
    const b0 = TABLES.FORD_BODY[vin.slice(2, 4)] || null;
    const e0 = TABLES.FORD_ENGINE[vin[4]] || [];
    const narrowed = yrs.filter((y) =>
      (!pyBool(b0) || b0.some(([a, z]) => a <= y && y <= z)) &&
      e0.some(([a, z]) => a <= y && y <= z)
    );
    if (narrowed.length === 1) {
      year = narrowed[0];
      r.notes.push(`Decade resolved to ${year} from body/engine code validity.`);
    }
  }
  r.year = year;
  r.year_candidates = yrs;
  if (!year && yrs.length > 1) flag(r, "warn", `Year digit '${yd}' is ambiguous (${pyInterp(yrs)}); pass --year to resolve.`);
  addField(r, "year", yd, pyInterp(year || yrs), "S9");
  r.plant = get(TABLES.FORD_PLANTS, vin[1]);
  addField(r, "plant", vin[1], r.plant || "unknown", "S10/S11");
  if (!r.plant) flag(r, "error", `Unknown Ford plant '${vin[1]}'.`);
  const body = vin.slice(2, 4);
  const wins = TABLES.FORD_BODY[body] || [];
  const y = year || (yrs.length ? yrs[0] : null);
  const [txt, bsrc] = fordBody(body, y);
  if (txt) {
    r.body_style = txt;
    r.model_series = fordSeriesName(txt);
    r.make = txt.includes("Mercury") ? "Mercury" : "Ford";
  } else if (pyBool(wins)) {
    r.make = "Ford/Mercury";
    r.model_series = `body serial ${body}`;
    const spans = wins.map(([a, z, t]) => `${a}-${z} ${t}`).join(", ");
    flag(r, "error", `Body code ${body} not used in ${pyInterp(y)} (known uses: ${spans}).`);
  } else {
    r.make = "Ford/Mercury";
    r.model_series = `body serial ${body} (not in loaded tables)`;
    flag(r, "warn", `Body serial '${body}' not in loaded tables (Mustang/Cougar, 1968-71 Fairlane/Torino, 1968 full-size Ford).`);
  }
  addField(r, "body", body, r.body_style || "unknown", bsrc || "S9/S16/S17");
  const eng = vin[4];
  let m = null;
  for (const [a, z, meaning] of TABLES.FORD_ENGINE[eng] || []) {
    if (y && a <= y && y <= z) m = meaning;
  }
  r.engine = m;
  addField(r, "engine", eng, m || "unknown for this year", "S9/S11");
  if (!m) flag(r, "warn", `Engine code '${eng}' not documented for ${pyInterp(y)} in loaded table.`);
  r.sequence = vin.slice(5);
  addField(r, "sequence", r.sequence, "consecutive unit number", "S9");
  if (!isDigits(r.sequence)) flag(r, "error", "Unit number (positions 6-11) must be digits.");
  if (((body === "45" || body === "46") && y === 1969) || (body === "38" && (y === 1970 || y === 1971))) {
    r.notes.push("Cobra body serial: high-value configuration; confirm engine code and Marti Report before valuing.");
  }
  if (vin[1] === "S" && body === "09" && (y === 1965 || y === 1966)) {
    r.notes.push("Plant S (Allen Park) is associated with 1965-66 Shelby GT350 provenance; verify with SAAC registry.");
  }
}

function decodeMopar(vin, r, hint) {
  const early = isDigits(vin[6]);
  r.family = early ? "Chrysler 13-char (1966-67 tables)" : "Chrysler 13-char (1968-74 tables)";
  const makes = { B: "Plymouth", R: "Plymouth", V: "Plymouth", P: "Plymouth", C: "Chrysler", Y: "Imperial" };
  r.make = Object.prototype.hasOwnProperty.call(makes, vin[0]) ? makes[vin[0]] : ("LWXJD".includes(vin[0]) ? "Dodge" : null);
  const yd = vin[5];
  const [year, yrs] = decade(yd, early ? [1966, 1967] : range(1968, 1975), hint);
  r.year = year;
  r.year_candidates = yrs;
  if (!pyBool(yrs)) flag(r, "error", `Year digit '${yd}' not valid for a ${early ? "1966-67" : "1968-74"} Chrysler VIN (plant code '${vin[6]}').`);
  else if (!year && yrs.length > 1) flag(r, "warn", `Year digit '${yd}' ambiguous (${pyInterp(yrs)}); pass --year.`);
  addField(r, "year", yd, pyInterp(year || yrs), "S18");
  const line = get(TABLES.MOPAR_LINE, vin[0]);
  const cls = get(TABLES.MOPAR_CLASS, vin[1]);
  const name = year === 1969 ? get(TABLES.MOPAR_MODELNAME, vin.slice(0, 2)) : null;
  r.model_series = line && cls ? `${name || line} (${cls} price class)` : null;
  addField(r, "car_line", vin[0], line || "unknown", "S12/S18");
  addField(r, "price_class", vin[1], cls || "unknown", "S12/S15/S18");
  if (!line) flag(r, "error", `Unknown car line '${vin[0]}'.`);
  if (!cls) flag(r, "error", `Unknown price class '${vin[1]}'.`);
  if (vin[0] === "J" && year && year < 1970) flag(r, "error", "Challenger (J) did not exist before 1970.");
  if (vin[0] === "X" && year && year > 1970) flag(r, "error", "Car line X (Charger) not used after 1970; 1971+ Chargers are W.");
  if (vin[1] === "O" && year && year > 1967) flag(r, "warn", "Price class O (Super Stock) is listed only for 1966-67.");
  r.body_style = get(TABLES.MOPAR_BODY, vin.slice(2, 4));
  addField(r, "body", vin.slice(2, 4), r.body_style || "unknown", "S12/S18");
  if (!r.body_style) flag(r, "error", `Unknown body code '${vin.slice(2, 4)}'.`);
  const y = year || (yrs.length ? yrs[0] : null);
  const eng = vin[4];
  const tbl = (y != null && TABLES.MOPAR_ENGINE[String(y)]) || {};
  r.engine = get(tbl, eng);
  addField(r, "engine", eng, r.engine || "unknown / table not loaded", "S18/S12");
  if (!pyBool(tbl)) flag(r, "warn", `Mopar engine table for ${pyInterp(y)} not loaded; engine code shown raw.`);
  else if (!r.engine) flag(r, "error", `Engine code '${eng}' not valid for ${pyInterp(y)}.`);
  const plants = early ? TABLES.MOPAR_PLANTS_6667 : TABLES.MOPAR_PLANTS;
  r.plant = get(plants, vin[6]);
  addField(r, "plant", vin[6], r.plant || "unknown", "S18");
  if (!r.plant) flag(r, "error", `Unknown Chrysler plant '${vin[6]}'.`);
  r.sequence = vin.slice(7);
  addField(r, "sequence", r.sequence, "sequence (serial) number", "S18");
  if (!isDigits(r.sequence)) flag(r, "error", "Sequence must be 6 digits.");
  if (r.engine && r.engine.includes("Hemi")) {
    r.notes.push("Hemi engine code: high-value, high-fraud configuration. Human review required.");
  }
}

function setdefault(obj, key, value) {
  if (!Object.prototype.hasOwnProperty.call(obj, key)) obj[key] = value;
  return obj[key];
}

function decodeTag(tag, r) {
  const t = tag.toUpperCase();
  const out = { raw: tag, checks: [] };
  const cowl = t.match(/\bST\s*(\d{2})-(\d)(\d{2})(\d{2})/);
  if (cowl) {
    const yy = cowl[1];
    const div = cowl[2];
    const ser = cowl[3];
    const body = cowl[4];
    out.kind = "GM cowl tag";
    out.year = 1900 + Number(yy);
    out.division = div;
    out.series = ser;
    out.body = body;
    if (r.year && 1900 + Number(yy) !== r.year) flag(r, "error", `Cowl tag year 19${yy} != VIN year ${r.year}.`);
    if (r.input.slice(0, 1) !== div) flag(r, "error", "Cowl tag division digit does not match VIN.");
    if (isDigits(r.input.slice(1, 3)) && r.input[1] !== ser[0]) flag(r, "error", `Cowl tag series ${div}${ser} conflicts with VIN.`);
    if (isDigits(r.input.slice(3, 5)) && r.input.slice(3, 5) !== body) flag(r, "error", `Cowl tag body ${body} != VIN body ${r.input.slice(3, 5)}.`);
    out.checks.push("year/division/series/body compared with VIN");
  }
  for (const [code, txt] of Object.entries(TABLES.MOPAR_FENDER_ENGINE)) {
    if (new RegExp(`\\b${code}\\b`).test(t)) {
      setdefault(out, "kind", "Mopar fender tag");
      out.engine_sales_code = `${code} = ${txt}`;
      if (r.family.startsWith("Chrysler")) {
        const y = r.year != null ? r.year : (r.year_candidates.length ? r.year_candidates[0] : null);
        const ok = [];
        for (const [a, z, chars] of TABLES.MOPAR_E_TO_VIN[code] || []) {
          if (y && a <= y && y <= z) ok.push(chars);
        }
        if (ok.length === 0) flag(r, "warn", `Fender tag ${code} has no VIN cross-reference loaded for ${pyInterp(y)}.`);
        else if (!new Set(ok.flat()).has(r.input[4])) {
          flag(r, "error", `Fender tag ${code} (${txt}) conflicts with VIN engine code '${r.input[4]}' for ${pyInterp(y)}.`);
        }
      }
    }
  }
  const plate = t.match(/\b(\d[A-Z]\d{2}[A-Z]\d{6})\b/);
  if (plate) {
    setdefault(out, "kind", "Ford door data plate");
    out.plate_vin = plate[1];
    if (plate[1] !== r.input) flag(r, "error", `Door plate VIN ${plate[1]} != VIN ${r.input}.`);
  }
  setdefault(out, "kind", "unrecognised");
  r.tag = out;
  if (out.kind === "unrecognised") flag(r, "warn", "Tag text not recognised; no cross-check performed.");
}

function score(r) {
  const keys = [r.year, r.make, r.model_series, r.body_style, r.engine, r.plant, r.sequence];
  let s = keys.filter((k) => pyBool(k)).length / keys.length;
  const errs = r.flags.filter((f) => f.severity === "error").length;
  const warns = r.flags.filter((f) => f.severity === "warn").length;
  s = Math.max(0, s - 0.35 * errs - 0.1 * warns);
  if (r.tag && r.tag.kind !== "unrecognised" && errs === 0) s = Math.min(1, s + 0.05);
  r.confidence_score = roundHalfEven(s, 2);
  r.confidence = s >= 0.85 && errs === 0 ? "high" : s >= 0.55 && errs === 0 ? "medium" : "low";
  return r;
}

export function decode(vin, yearHint = null, tag = null) {
  const raw = vin;
  vin = raw.toUpperCase().replace(/[\s\-]/g, "");
  const r = makeResult(vin);
  if (vin !== raw.toUpperCase().trim()) r.notes.push("Spaces/dashes removed from input.");
  if (!/^[A-Z0-9]+$/.test(vin || "-")) {
    flag(r, "error", "VIN contains illegal characters.");
    return score(r);
  }
  if (vin.length === 17) {
    flag(r, "error", "17-character VIN = 1981 or later; outside 1964-80 scope.");
    return score(r);
  }
  if (vin.length === 11 && isDigits(vin[0]) && isAlpha(vin[1])) decodeFord(vin, r, yearHint);
  else if (vin.length === 13 && "12".includes(vin[0])) decodeGm(vin, r, yearHint);
  else if (vin.length === 13 && isAlpha(vin[0])) decodeMopar(vin, r, yearHint);
  else if (vin.length === 12 && vin[0] === "4") {
    r.family = "Chevrolet 1964 12-char (structure only)";
    r.year = 1964;
    r.make = "Chevrolet";
    r.plant = get(TABLES.CHEV_PLANTS, vin[5]);
    r.sequence = vin.slice(6);
    flag(r, "warn", "1964 Chevrolet format decoded structurally only.");
  } else {
    flag(r, "error", `Length ${vin.length} / pattern does not match any supported 1964-80 GM, Ford or Mopar format.`);
  }
  if (yearHint && r.year && yearHint !== r.year) flag(r, "error", `Claimed year ${yearHint} != VIN year ${r.year}.`);
  if (yearHint && pyBool(r.year_candidates) && !r.year_candidates.includes(yearHint)) {
    flag(r, "error", `Claimed year ${yearHint} impossible for this VIN (candidates ${pyInterp(r.year_candidates)}).`);
  }
  if (r.year && !(r.year >= 1964 && r.year <= 1980)) flag(r, "error", "Year outside 1964-80 scope.");
  if (tag) decodeTag(tag, r);
  return score(r);
}
