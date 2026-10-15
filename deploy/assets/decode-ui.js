import { decode } from "./decoder.js";

const form = document.getElementById("decode-form");
const resultSection = document.getElementById("decode-result");
const resultInner = document.getElementById("decode-result-inner");
const formError = document.getElementById("decode-error");

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[c]));
}

function enginePlain(engine) {
  if (!engine) return "Not in the loaded tables for this year";
  if (engine.includes("NOT encoded")) {
    return "V8. This VIN does not record the displacement, so it cannot say 396, 427, 454, or any other size.";
  }
  if (engine.startsWith("6-cylinder")) return "6-cylinder. This VIN does not record the displacement.";
  if (engine.startsWith("not encoded in 1965-71 Pontiac")) {
    return "Not in the VIN. On these Pontiacs the engine size is on the block, not in the serial number.";
  }
  if (engine.includes("not yet loaded")) return "The engine letter is in the VIN. The 1972-1980 Pontiac engine table is not loaded yet.";
  return engine;
}

function seriesPlain(series) {
  if (!series) return "Unknown";
  const pontiac = series.match(/^Pontiac series '([^']+)'/);
  if (pontiac) return `Series ${pontiac[1]}. The 1972-1980 Pontiac name table is not loaded yet.`;
  if (series.startsWith("body serial ")) return "Body code " + series.slice("body serial ".length);
  return series;
}

function titleFor(r) {
  if (r.family === "unknown") return "We can't decode this VIN";
  const bits = [];
  if (r.year) bits.push(String(r.year));
  else if (r.year_candidates.length) bits.push(r.year_candidates.join(" or "));
  if (r.make) bits.push(r.make);
  if (r.model_series && !r.model_series.startsWith("body serial") && !r.model_series.startsWith("Pontiac series")) {
    bits.push(r.model_series);
  }
  return bits.join(" ") || "Partial decode";
}

function confidenceCopy(r) {
  const warns = r.flags.filter((f) => f.severity === "warn").length;
  const errors = r.flags.filter((f) => f.severity === "error").length;
  if (r.family === "unknown") {
    return "This does not match a 1964-1980 Chevrolet, Pontiac, Ford, Mercury, Dodge, or Plymouth VIN we can read.";
  }
  if (r.confidence === "high" && warns === 0) {
    return "The VIN matches a format we know, and every field decoded with no conflicts. That still does not prove options, originality, or what the car is worth.";
  }
  if (r.confidence === "high") {
    return "The format matches, with a warning. Read it before you rely on the decode. A VIN still can't prove an option package.";
  }
  if (r.confidence === "medium") {
    return "Most of the VIN decoded, and nothing directly conflicted, but a year, code, or table is incomplete. Treat this as a lead, not a verdict.";
  }
  if (errors) {
    return "Something conflicted or is not a valid code for this car. Don't treat this decode as proof of what the car is.";
  }
  return "Too little of this VIN could be read to rely on it.";
}

function unsupportedLead(r) {
  const msg = r.flags[0] ? r.flags[0].message : "";
  if (msg.includes("illegal characters")) {
    return "That doesn't look like a VIN. Use letters and numbers. Spaces and dashes are okay.";
  }
  if (msg.includes("17-character")) {
    return "That's a 17-character VIN, so it is 1981 or later. This free decoder stops at 1980.";
  }
  return "That length and pattern is not a 1964-1980 GM, Ford, or Mopar VIN this decoder supports. Covered makes are Chevrolet, Pontiac, Ford, Mercury, Dodge, and Plymouth.";
}

function carLabel(r) {
  const bits = [];
  if (r.year) bits.push(String(r.year));
  if (r.make) bits.push(r.make);
  if (r.model_series && !r.model_series.startsWith("body serial") && !r.model_series.startsWith("Pontiac series")) {
    bits.push(r.model_series);
  }
  let text = bits.join(" ");
  if (r.input) text = text ? `${text} · VIN ${r.input}` : `VIN ${r.input}`;
  return text.slice(0, 120);
}

function field(label, value, detail) {
  return `<div class="field"><dt>${esc(label)}</dt><dd>${esc(value)}</dd>${detail ? `<p class="field-detail">${esc(detail)}</p>` : ""}</div>`;
}

function list(items, cls) {
  if (!items.length) return "";
  return `<ul class="flags ${cls}">${items.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>`;
}

function render(r, enteredYear, enteredTag) {
  const errors = r.flags.filter((f) => f.severity === "error").map((f) => f.message);
  const warns = r.flags.filter((f) => f.severity === "warn").map((f) => f.message);
  const car = carLabel(r);
  const known = r.family !== "unknown";
  const yearValue = r.year
    ? String(r.year)
    : (r.year_candidates.length ? r.year_candidates.join(" or ") : "Not determined");
  const yearDetail = !r.year && r.year_candidates.length > 1 ? "Add the model year above to pick one." : "";
  const tagAgrees = r.tag && r.tag.kind === "GM cowl tag" && !r.flags.some((f) => f.message.startsWith("Cowl tag"));
  const codes = Object.entries(r.fields).map(([key, fieldInfo]) => {
    const label = {
      division: "Division",
      year: "Year code",
      series: "Series",
      body: "Body",
      plant: "Plant",
      sequence: "Sequence",
      engine: "Engine",
      car_line: "Car line",
      price_class: "Price class",
    }[key] || key;
    return `<li><b>${esc(label)} ${esc(fieldInfo.value)}</b> — ${esc(fieldInfo.meaning)}</li>`;
  }).join("");

  const fields = known ? `
    <dl class="field-grid">
      ${field("Year", yearValue, yearDetail)}
      ${field("Make", r.make || "Unknown")}
      ${field("Model / series", seriesPlain(r.model_series))}
      ${field("Body", r.body_style || "Unknown")}
      ${field("Engine", enginePlain(r.engine))}
      ${field("Assembly plant", r.plant || "Unknown")}
      ${field("Sequence", r.sequence || "Unknown")}
    </dl>` : "";

  const notes = r.notes.length ? `<h3>Notes from this VIN</h3>${list(r.notes, "notes")}` : "";
  const conflictBlock = known && errors.length ? `<h3>Conflicts</h3>${list(errors, "errors")}` : "";
  const warnBlock = warns.length ? `<h3>Warnings</h3>${list(warns, "warns")}` : "";
  const tagLine = r.tag
    ? `<p class="fine">Trim tag checked: ${esc(r.tag.raw)}${r.tag.kind && r.tag.kind !== "unrecognised" ? ` (${esc(r.tag.kind)})` : ""}.</p>`
    : (enteredTag ? `<p class="fine">The trim tag was not checked, because this VIN was rejected before that step.</p>` : "");
  const agree = tagAgrees ? `<p>The cowl tag agrees with the VIN on year, division, series, and body.</p>` : "";
  const entered = enteredYear ? `<p class="fine">Model year you entered: ${esc(enteredYear)}.</p>` : "";
  const leadBits = [r.body_style, r.plant ? "built in " + r.plant : ""].filter(Boolean);
  const lead = known
    ? `<p class="result-lead">${esc(leadBits.join(", ") || "Part of this VIN decoded. The fields below are what we could read.")}</p>`
    : `<p class="result-lead">${esc(unsupportedLead(r))}</p>`;

  resultInner.innerHTML = `
    <article class="result-card ${known ? "" : "bad"}">
      <p class="vin-line">VIN <span>${esc(r.input || "—")}</span></p>
      <h2 id="decode-heading" tabindex="-1">${esc(titleFor(r))}</h2>
      ${lead}
      ${entered}
      <p class="conf ${esc(r.confidence)}"><b>Confidence: ${esc(r.confidence)}.</b> ${esc(confidenceCopy(r))}</p>
      ${fields}
      <aside class="honest"><b>A VIN can't prove an SS, Hemi, Judge, or similar package.</b> Those were often options, not their own series in the VIN. A matching number can be consistent with the car and still not prove the package, the engine size, or that the numbers are original.</aside>
      ${agree}
      ${notes}
      ${conflictBlock}
      ${warnBlock}
      ${tagLine}
      ${codes ? `<details class="codes"><summary>Codes read from this VIN</summary><ul>${codes}</ul></details>` : ""}
      <div class="decode-next">
        <h3>Want the full value report?</h3>
        <p>This free decode is the identification only. The report adds a check of the trim tag against photos, a matching-numbers checklist, and a value range from sold cars. Reports are not open yet.</p>
        <p class="prefill-note">The waitlist form below is filled in with <b>${esc(car)}</b>.</p>
        <a class="btn" href="#waitlist" data-waitlist data-car="${esc(car)}">Join the waitlist for the full value report</a>
      </div>
    </article>`;

  const carInput = document.querySelector('#waitlist input[name="car"]');
  if (carInput) carInput.value = car;
  resultSection.hidden = false;
  const heading = document.getElementById("decode-heading");
  if (heading) heading.focus({ preventScroll: true });
  resultSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  formError.textContent = "";
  const vin = form.vin.value;
  const yearRaw = form.year.value.trim();
  const tagRaw = form.tag.value.trim();
  let year = null;
  if (yearRaw) {
    if (!/^\d{4}$/.test(yearRaw)) {
      formError.textContent = "Enter a 4-digit model year, such as 1969, or leave the year blank.";
      form.year.focus();
      return;
    }
    year = Number(yearRaw);
  }
  try {
    render(decode(vin, year, tagRaw || null), yearRaw, tagRaw);
  } catch (err) {
    formError.textContent = "The decoder hit an unexpected error. Check the VIN and try again.";
  }
});

document.getElementById("try-sample").addEventListener("click", () => {
  form.vin.value = "136379A307416";
  form.year.value = "";
  form.tag.value = "";
  formError.textContent = "";
  form.requestSubmit();
});

resultSection.addEventListener("click", (event) => {
  const link = event.target.closest("[data-waitlist]");
  if (!link) return;
  const carInput = document.querySelector('#waitlist input[name="car"]');
  if (carInput && link.dataset.car) carInput.value = link.dataset.car;
  const email = document.getElementById("email");
  if (email) email.focus({ preventScroll: true });
});
