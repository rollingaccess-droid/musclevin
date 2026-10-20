"""The JavaScript decoder must match app/decoder.py on every VIN the Python tests use."""
import ast
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from decoder import decode

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEST_SRC = pathlib.Path(__file__).resolve().parent / "test_decoder.py"
RUNNER = pathlib.Path(__file__).resolve().parent / "run_js_decode.mjs"

# Cases the Python suite does not call, including invalid and edge VINs.
EXTRA = [
    {"vin": "", "year": None, "tag": None},
    {"vin": "   ", "year": None, "tag": None},
    {"vin": "---", "year": None, "tag": None},
    {"vin": "136379/A307416", "year": None, "tag": None},
    {"vin": "136379A307416!", "year": None, "tag": None},
    {"vin": "1G1YY 22G965104378", "year": None, "tag": None},
    {"vin": "1G1YY22G965104378", "year": 1969, "tag": None},
    {"vin": "HELLO", "year": None, "tag": None},
    {"vin": "12345", "year": None, "tag": None},
    {"vin": "136379A30741X", "year": None, "tag": None},
    {"vin": "13637XA307416", "year": None, "tag": None},
    {"vin": "336379A307416", "year": None, "tag": None},
    {"vin": "ZZ23H9G100001", "year": None, "tag": None},
    {"vin": "9F99Z123456", "year": None, "tag": None},
    {"vin": "1Q87HBL100000", "year": None, "tag": None},
    {"vin": "4ABCDA123456", "year": None, "tag": None},
    {"vin": "136379A307416", "year": 1969, "tag": None},
    {"vin": "136379A307416", "year": 1955, "tag": None},
    {"vin": "136379A307416", "year": None, "tag": "not a tag"},
    {"vin": "136379A307416", "year": None, "tag": "ST 68-13637"},
    {"vin": "136379A307416", "year": None, "tag": "ST 69-23637"},
    {"vin": "136379-A307416", "year": None, "tag": None},
    {"vin": "rm23h9g170193", "year": None, "tag": None},
    {"vin": "136379A307416\n", "year": None, "tag": None},
    {"vin": "RM23H9G100001", "year": None, "tag": "E22"},
    {"vin": "RM23H9G100001", "year": None, "tag": "E74 E85"},
    {"vin": "RO23H9G100001", "year": None, "tag": None},
    {"vin": "9F02R123456", "year": None, "tag": "DOOR 9F02R123456"},
    {"vin": "9F02R123456", "year": None, "tag": "DOOR 9F02R654321"},
    {"vin": "7F02C123456", "year": 1977, "tag": None},
    {"vin": "124375L123456", "year": None, "tag": None},
    {"vin": "242375A123456", "year": None, "tag": None},
    {"vin": "226379A123456", "year": None, "tag": None},
    {"vin": "136379A100000", "year": None, "tag": None},
    {"vin": "1363791100000", "year": None, "tag": None},
    {"vin": "2Q87H2N100000", "year": None, "tag": None},
    {"vin": "1Q87HAL100000", "year": None, "tag": None},
    {"vin": "6F02C123456", "year": None, "tag": None},
    {"vin": "S09F1234567", "year": None, "tag": None},
    {"vin": "136379A307416", "year": 1969, "tag": "ST 69-13637 ATL"},
]


def _calls_from_python_tests():
    tree = ast.parse(TEST_SRC.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "decode":
            continue
        if len(node.args) != 1:
            raise AssertionError("decode() call has an unexpected shape")
        vin = ast.literal_eval(node.args[0])
        year = None
        tag = None
        for kw in node.keywords:
            if kw.arg == "year_hint":
                year = ast.literal_eval(kw.value)
            elif kw.arg == "tag":
                tag = ast.literal_eval(kw.value)
            else:
                raise AssertionError(f"unexpected decode() keyword {kw.arg}")
        found.append({"vin": vin, "year": year, "tag": tag})
    return found


def cases():
    found = _calls_from_python_tests()
    src = TEST_SRC.read_text(encoding="utf-8")
    assert src.count("decode(") == len(found), "a decode() call was not extracted"
    assert any(c["vin"] == "136379A307416" for c in found)
    seen = set()
    out = []
    for case in found + EXTRA:
        key = (case["vin"], case["year"], case["tag"])
        if key in seen:
            continue
        seen.add(key)
        out.append(case)
    return out


def _diff(py, js, path="$"):
    if isinstance(py, bool) or isinstance(js, bool):
        if py != js:
            return [f"{path}: {py!r} != {js!r}"]
        return []
    if isinstance(py, (int, float)) and isinstance(js, (int, float)):
        if py != js:
            return [f"{path}: {py!r} != {js!r}"]
        return []
    if isinstance(py, dict) and isinstance(js, dict):
        msgs = []
        for key in list(py) + [k for k in js if k not in py]:
            if key not in js:
                msgs.append(f"{path}.{key}: missing in JS")
            elif key not in py:
                msgs.append(f"{path}.{key}: unexpected in JS ({js[key]!r})")
            else:
                msgs.extend(_diff(py[key], js[key], f"{path}.{key}"))
        return msgs
    if isinstance(py, list) and isinstance(js, list):
        if len(py) != len(js):
            return [f"{path}: length {len(py)} != {len(js)} ({py!r} vs {js!r})"]
        msgs = []
        for i, (a, b) in enumerate(zip(py, js)):
            msgs.extend(_diff(a, b, f"{path}[{i}]"))
        return msgs
    if py != js:
        return [f"{path}: {py!r} != {js!r}"]
    return []


def test_every_python_test_vin_is_in_the_parity_set():
    vins = {c["vin"] for c in _calls_from_python_tests()}
    assert "136379A307416" in vins
    assert "1G1YY22G965104378" in vins
    assert len(vins) >= 20


def test_js_decoder_matches_python():
    batch = cases()
    proc = subprocess.run(
        ["node", str(RUNNER)],
        input=json.dumps(batch),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    got = json.loads(proc.stdout)
    assert len(got) == len(batch)
    mismatches = []
    for case, js in zip(batch, got):
        py = decode(case["vin"], case["year"], case["tag"]).to_dict()
        msgs = _diff(py, js)
        if msgs:
            mismatches.append((case, msgs[:12]))
    assert not mismatches, json.dumps(mismatches[:8], indent=2)


def test_js_tables_match_python():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "deploy" / "build_decoder_data.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_inline_worker_embeds_deploy_assets_and_waitlist():
    import base64

    text = (ROOT / "deploy" / "_worker_inline.js").read_text(encoding="utf-8")
    line, _, handler = text.partition("\n")
    assert line.startswith("const ASSETS_INLINE = ") and line.endswith(";")
    assets = json.loads(line[len("const ASSETS_INLINE = "):-1])
    expect = {
        "/index.html": ROOT / "deploy" / "index.html",
        "/assets/style.css": ROOT / "deploy" / "assets" / "style.css",
        "/assets/decoder-data.js": ROOT / "deploy" / "assets" / "decoder-data.js",
        "/assets/decoder.js": ROOT / "deploy" / "assets" / "decoder.js",
        "/assets/decode-ui.js": ROOT / "deploy" / "assets" / "decode-ui.js",
        "/assets/sample-report-1.png": ROOT / "deploy" / "assets" / "sample-report-1.png",
        "/assets/sample-report.pdf": ROOT / "deploy" / "assets" / "sample-report.pdf",
        "/assets/favicon.svg": ROOT / "deploy" / "assets" / "favicon.svg",
        "/favicon.ico": ROOT / "deploy" / "favicon.ico",
        "/apple-touch-icon.png": ROOT / "deploy" / "apple-touch-icon.png",
        "/robots.txt": ROOT / "deploy" / "robots.txt",
        "/sitemap.xml": ROOT / "deploy" / "sitemap.xml",
        "/llms.txt": ROOT / "deploy" / "llms.txt",
        "/guides/1969-chevelle-vin.html": ROOT / "deploy" / "guides" / "1969-chevelle-vin.html",
    }
    assert set(assets) == set(expect)
    for url, path in expect.items():
        ctype, b64 = assets[url]
        assert ctype
        assert base64.b64decode(b64) == path.read_bytes()
    for name in ("_worker.js", "_worker_inline.js"):
        worker = (ROOT / "deploy" / name).read_text(encoding="utf-8")
        assert 'url.pathname === "/api/waitlist"' in worker
        assert "function onRequestPost" in worker or "async function onRequestPost" in worker
    assert "async function onRequestPost" in handler
    assert "env.ASSETS.fetch" not in handler
