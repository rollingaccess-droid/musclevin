# MuscleVIN

Prototype for decoding classic and muscle-car VINs and trim tags, plus the landing page and Cloudflare deploy for the waitlist.

## Layout

| Path | What it is |
|---|---|
| `app/` | Python VIN and trim-tag decoder. `decoder.py` is the decoder (stdlib only). `tests/test_decoder.py` is the pytest suite. `make_report.py` renders a sample PDF. `app/README.md` has coverage, sources, and known limits. |
| `site/` | Original static landing page. The waitlist form is a placeholder and does not submit anywhere. |
| `deploy/` | Cloudflare version of the same page. The form posts to `/api/waitlist`. The free VIN decoder is client-side: `assets/decoder.js` (port of `app/decoder.py`), `assets/decoder-data.js` (tables generated from Python), and `assets/decode-ui.js`. |
| `plan.md` | Business plan. |
| `sample-report.pdf` | Sample report. The same file is also under `site/assets/` and `deploy/assets/`. |

`deploy/_worker.js` is the Pages worker. It serves the site through the `ASSETS` binding and handles `POST /api/waitlist`. Signups are stored in the KV binding `WAITLIST`. When `RESEND_API_KEY` and `RESEND_SEGMENT_ID` are set, the worker also adds the address to that Resend segment. If those variables are unset, the signup stays in KV and the Resend call is skipped.

`deploy/_worker_inline.js` is the same handler with the site files inlined, so it can be uploaded as a single Worker script without an `ASSETS` binding. It still expects the `WAITLIST` binding and the same Resend variables.

`deploy/functions/api/waitlist.js` is a Pages Functions handler that writes the waitlist to KV only.

## Decoder tests

Python 3.10 or newer (the decoder uses `X | None` syntax). `reportlab` is only needed to generate the PDF.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pytest reportlab
cd app
python -m pytest -q tests
python make_report.py ../sample-report.pdf
```

GitHub Actions (`.github/workflows/decoder-tests.yml`) runs `pytest` on every push and pull request. That includes `app/tests/test_js_parity.py`, which checks the JavaScript decoder against `app/decoder.py` for every VIN in the Python tests plus invalid cases. Node 22 is required for that test. The workflow does not deploy.

After a table change in `app/decoder.py`, regenerate the browser tables and the single-file worker, then re-run the tests:

```bash
python3 deploy/build_decoder_data.py
python3 deploy/build_inline_worker.py
cd app && python -m pytest -q tests
```

## Deploys

There is no CI token yet. Deploys are done by the operator through the Cloudflare API.

The live worker needs:

- a KV namespace bound as `WAITLIST`
- `RESEND_API_KEY`
- `RESEND_SEGMENT_ID`

Keep those values in the Cloudflare environment. Do not commit them. `.env` files are gitignored.
