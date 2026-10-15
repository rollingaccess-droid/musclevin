"""Render the sample PDF report from live decoder output."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).parent))
from datetime import date
from decoder import decode
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

VIN, TAG = "136379A307416", "ST 69-13637 ATL BDY"
r = decode(VIN, year_hint=1969, tag=TAG)
NAVY, RED, GREY = colors.HexColor("#14213d"), colors.HexColor("#b00020"), colors.HexColor("#f2f2f2")
ss = getSampleStyleSheet()
H1 = ParagraphStyle("h1", parent=ss["Title"], textColor=NAVY, fontSize=22)
H2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=NAVY, spaceBefore=12)
B = ParagraphStyle("b", parent=ss["BodyText"], fontSize=9.5, leading=13)
S = ParagraphStyle("s", parent=B, fontSize=8, leading=10, textColor=colors.HexColor("#444444"))
W = ParagraphStyle("w", parent=B, textColor=colors.white, fontName="Helvetica-Bold", alignment=1, fontSize=11)

def tbl(rows, widths, header=True, bg=None):
    HW = ParagraphStyle("hw", parent=B, textColor=colors.white, fontName="Helvetica-Bold")
    t = Table([[Paragraph(str(c), HW if (header and i == 0) else B) for c in row] for i, row in enumerate(rows)], colWidths=widths)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")), ("VALIGN", (0, 0), (-1, -1), "TOP")]
    if header: st += [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white)]
    if bg: st += [("BACKGROUND", (0, 1), (-1, -1), bg)]
    t.setStyle(TableStyle(st)); return t

def banner(text, color=RED):
    t = Table([[Paragraph(text, W)]], colWidths=[7 * inch]); t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), color), ("TOPPADDING", (0,0),(-1,-1),6), ("BOTTOMPADDING",(0,0),(-1,-1),6)])); return t

def footer(c, d):
    c.saveState(); c.setFont("Helvetica", 7); c.setFillColor(colors.grey)
    c.drawString(0.75 * inch, 0.5 * inch, "SAMPLE REPORT - not a certified appraisal. Prototype output; value data is EXAMPLE DATA - comps source pending license.")
    c.drawRightString(7.75 * inch, 0.5 * inch, f"Page {d.page}"); c.restoreState()

DISCLAIMER = ("This report is an informational market estimate based on publicly reported sales and the information and photos you "
 "provided. It is not a certified or USPAP-compliant appraisal, an inspection, or a guarantee of authenticity, originality, or "
 "value, and must not be relied on for insurance, tax, legal, estate, or lending purposes. Verify with a qualified appraiser and "
 "factory documentation (e.g., Marti, PHS). Liability is limited to the price paid.")

st = []
st += [Paragraph("What Is It &amp; What's It Worth?", H1), Paragraph("Classic / Muscle Car Identification &amp; Value Report", ss["Heading3"]),
       banner("SAMPLE REPORT &middot; NOT A CERTIFIED APPRAISAL", NAVY), Spacer(1, 8)]
st.append(tbl([["Subject vehicle (as claimed)", "1969 Chevrolet Chevelle SS 396, 2-door sport coupe"],
               ["VIN examined", f"{VIN} (example VIN published at chevellestuff.net; used for illustration only)"],
               ["Cowl tag text (sample)", TAG], ["Report date", date.today().strftime("%B %d, %Y")],
               ["Decode confidence", f"{r.confidence.upper()} ({r.confidence_score:.2f}) - VIN structure"],
               ["SS 396 status", "<b>CONSISTENT BUT UNVERIFIED</b> - the VIN cannot prove SS 396 for 1969 (see 2.2)"]],
              [2.1 * inch, 4.9 * inch], header=False))
st.append(Paragraph("1. Summary", H2))
st.append(Paragraph("The VIN decodes cleanly to a 1969 Chevrolet Chevelle Malibu V8 two-door sport coupe built at Atlanta, GA, with no structural "
    "errors, and the sample cowl tag agrees with it on year, division, series and body. For 1969, Chevrolet sold the SS 396 as an option package "
    "(RPO Z25) on 136-series cars, so the VIN alone cannot confirm SS 396. Before treating the car as a real SS, it needs the documents and "
    "stamped numbers listed in Section 3.", B))
st.append(Paragraph("2. VIN decode", H2))
rows = [["Position", "Value", "Meaning", "Source"]]
order = [("division", "1"), ("series", "2-3"), ("body", "4-5"), ("year", "6"), ("plant", "7"), ("sequence", "8-13")]
for k, pos in order:
    f = r.fields[k]; rows.append([pos, f["value"], f["meaning"], f["source"]])
st.append(tbl(rows, [0.8 * inch, 0.9 * inch, 4.1 * inch, 1.2 * inch]))
st.append(Spacer(1, 6))
st.append(tbl([["Field", "Result"], ["Year", r.year], ["Make", r.make], ["Model / series", r.model_series], ["Body style", r.body_style],
               ["Engine (from VIN)", r.engine], ["Assembly plant", r.plant], ["Sequence no.", r.sequence]], [2.1 * inch, 4.9 * inch]))
fl = r.flags or [{"severity": "ok", "message": "No VIN/tag inconsistencies detected."}]
st.append(PageBreak()); st.append(Paragraph("2.1 Flags", ss["Heading4"]))
st.append(tbl([["Severity", "Message"]] + [[f["severity"].upper(), f["message"]] for f in fl], [1.0 * inch, 6.0 * inch]))
st.append(Paragraph("2.2 Notes", ss["Heading4"]))
for n in r.notes: st.append(Paragraph("&bull; " + n, B))
st.append(Paragraph("3. Matching numbers: what it means and what to check", H2))
st.append(Paragraph("A car is called <i>numbers-matching</i> when its major drivetrain parts are the ones it left the factory with, or are period-correct "
    "and stamped to match. For a 1969 Chevelle, Chevrolet stamped a VIN derivative (usually the year, plant and sequence, e.g. "
    "<b>9A307416</b> here) on the engine block pad and on some transmissions, plus an assembly-plant code, build date and a suffix code for "
    "the engine and transmission application. Casting numbers and date codes on the block, heads, intake, carburetor, rear axle and "
    "transmission should come shortly before the car's build date. Restamped pads and reproduction tags are known problems, so the "
    "report grades each item and never certifies authenticity.", B))
st.append(Spacer(1, 6))
st.append(tbl([["Item", "Expected for this VIN", "Status (sample)"],
    ["Engine pad VIN derivative", "Should read 9A307416 (year / plant / sequence)", "UNVERIFIABLE - photo needed"],
    ["Engine suffix code", "Must be a 396 suffix appropriate to an SS 396 application", "UNVERIFIABLE - photo needed"],
    ["Block casting no. &amp; date", "396 block casting dated before the car's build date", "UNVERIFIABLE"],
    ["Cowl tag", "Style 69-13637; tag year/series/body agree with the VIN", "MATCH (sample tag text)"],
    ["Transmission stamp", "VIN derivative and code consistent with factory unit", "UNVERIFIABLE"],
    ["Rear axle code / date", "Code consistent with SS ratio and date", "UNVERIFIABLE"],
    ["Build sheet / Protect-O-Plate", "Shows Z25 SS 396 option and original engine/trans", "NOT PROVIDED"]],
    [2.0 * inch, 3.3 * inch, 1.7 * inch]))
st.append(Paragraph("Recommendation: send clear photos of the engine stamp pad, the cowl tag and the axle code. Any original build sheet, "
    "Protect-O-Plate or dealer invoice is the strongest evidence. A real SS 396 commonly sells for much more than a Malibu clone, "
    "so this is the item that changes the value most.", B))
st.append(Paragraph("4. Value range", H2))
st.append(banner("EXAMPLE DATA - comps source pending license"))
st.append(Paragraph("<b>The figures below are placeholders that show the report layout. They are NOT real sales, NOT market data, and NOT an "
    "opinion of value for any car.</b> Live reports will use only licensed comp data (e.g., a licensed aggregator API) or comps the customer supplies.", B))
st.append(Spacer(1, 4))
st.append(tbl([["Scenario (EXAMPLE DATA)", "Low", "Mid", "High"],
    ["Verified SS 396, driver condition", "$XX,000 (example)", "$XX,000 (example)", "$XX,000 (example)"],
    ["SS 396 unverified / Malibu V8", "$XX,000 (example)", "$XX,000 (example)", "$XX,000 (example)"]],
    [2.8 * inch, 1.4 * inch, 1.4 * inch, 1.4 * inch], bg=colors.HexColor("#fdecea")))
st.append(Spacer(1, 4))
st.append(tbl([["Comp # (EXAMPLE DATA)", "Description", "Sale", "Source"]] +
    [[f"Example {i}", "1969 Chevelle SS 396 coupe - placeholder", "-- pending --", "comps source pending license"] for i in (1, 2, 3)],
    [1.5 * inch, 2.9 * inch, 1.1 * inch, 1.5 * inch], bg=colors.HexColor("#fdecea")))
st.append(Paragraph("Value confidence: <b>NOT RATED</b>. No licensed comps are loaded, so no range is given.", B))
st.append(Paragraph("5. Next steps", H2))
for n in ["Provide engine pad, cowl tag and axle photos to grade the matching-numbers table.",
          "Look for the build sheet (often found under the rear seat or on top of the fuel tank) or the Protect-O-Plate.",
          "For an insurance, estate or tax value, hire a certified (USPAP) appraiser."]:
    st.append(Paragraph("&bull; " + n, B))
st.append(KeepTogether([Paragraph("Disclaimer", H2), Paragraph(DISCLAIMER, S),
    Paragraph("Decoding rules come from the public sources listed in the decoder README (chevellestuff.net, macswebs.com ChevelleWorld). "
              "The prototype was generated automatically and has not been reviewed by a person.", S)]))
SimpleDocTemplate(sys.argv[1] if len(sys.argv) > 1 else "sample-report.pdf", pagesize=letter, leftMargin=0.75*inch, rightMargin=0.75*inch,
                  topMargin=0.7*inch, bottomMargin=0.8*inch, title="Sample Report - 1969 Chevelle SS 396").build(st, onFirstPage=footer, onLaterPages=footer)
