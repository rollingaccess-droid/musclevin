// Read a JSON list of {vin, year, tag} on stdin and write decode() results.
import { readFileSync } from "node:fs";
import { decode } from "../../deploy/assets/decoder.js";

const cases = JSON.parse(readFileSync(0, "utf8"));
const out = cases.map((c) => decode(c.vin, c.year ?? null, c.tag ?? null));
process.stdout.write(JSON.stringify(out));
