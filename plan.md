# Launch Plan: "What Is It & What's It Worth?" Classic/Muscle Car Report
Owner: Eric Anderson · Draft 2026-10-15 · Agent-run, with a human on call for edge cases

## 1. Competitors & the gap
| Competitor | What you get | Price | Source |
|---|---|---|---|
| Hagerty Valuation Tools | Condition #1–#4 values by model. Free tier and free account; Drivers Club gets unlimited lookups and 15+ yrs of history | Free; Club ~$70/yr | hagerty.com/media/market-trends/valuation/how-much-is-your-classic-car-worth/ · newsroom.hagerty.com (2022 refresh release) · hagerty.com/drivers-club/marketing/roadside |
| J.D. Power (ex-NADA) classic guide | Low/avg/high retail for 1926–2005, aimed at dealers and lenders. Free NADA classic lookup is gone | ~$230/yr (third-party figure) | jdpowervalues.com/get-values/classic-collectible-exotic-and-muscle-car-appraisal-guide · wcshipping.com/blog/tools-to-find-classic-car-values |
| Classic.com | Model benchmarks and comps. API is partner-only, quote on request | Free tier; API not priced publicly | support.classic.com/classic.com-api |
| Marti Report (Ford 1967–2020) | Factory build data, licensed from Ford | Standard $20 / Deluxe $55 / Elite $300 | martiauto.com/martireports.cfm · hagerty.com/media/.../kevin-marti-... |
| PHS (Pontiac 1961–86) | Factory invoice and option decode | ~$95–165 via resellers and forum reports | restoreamusclecar.com/parts/p/pontiac-historical-records · forums.maxperformanceinc.com/forums/showthread.php?t=860082 |
| ClassicDecoder (pre-1981 VINs) | Free basic decode; history report or build sheet | $29.99 | classicdecoder.com/pricing |
| Free comp tools (Old Cars Data, DriveIndex) | Auction-sale ranges by model/year. DriveIndex shows a flat ±12% band | Free | oldcarsdata.com/classic-car-value · driveindex.com/whats-my-car-worth |

**The gap:** every tool above answers only one question. Hagerty, J.D. Power and DriveIndex value a *model* but don't check *this car*. Marti, PHS and ClassicDecoder confirm *build data*, but each covers one make, takes days, and gives no value. Nobody offers a single, fast, plain-English answer that covers all makes:
- "What is my car (VIN + tag + photos), and does it match?"
- "Here are the real sold comps for cars like it, and a value range with stated confidence."

This fits the people posting about inherited cars: they don't know which tool to use, and the decoders they try disagree.

## 2. Sources for sold comps
| Source | Access | ToS / risk | Plan |
|---|---|---|---|
| Bring a Trailer | Public results pages | ToS bans scrapers, crawlers and data aggregation, plus use of its content for AI/RAG without written permission (bringatrailer.com/terms-of-use/) | **Do not scrape.** Link to it. Allow comps the user pastes in themselves |
| Mecum | Public results | ToS bans scraping, automated devices and AI access (mecum.com/terms/) | Do not scrape. Use only through a licensed aggregator |
| Barrett-Jackson | Public results | No terms reviewed. Assume restrictive | Same as Mecum |
| Classic.com | Partner API with up to 5 yrs of sales history | Licensed, so clean (support.classic.com/classic.com-api) | **Week 1: email datasupport@classic.com for a quote** |
| Old Cars Data | Free site plus an API/MCP. Says it aggregates BaT, Mecum, B-J and others | Read its API terms and confirm commercial use before relying on it (oldcarsdata.com/classic-car-value) | Best candidate for the MVP comp feed |
| eBay sold | Marketplace Insights API covers 90 days of sold items. Limited release, select partners only | Do not scrape | Skip for the MVP |
| Build data | Marti, PHS, Govier | Licensed sellers | Resell or refer for affiliate revenue. Never imitate their data |

Core rule: **use only licensed APIs or data the user provides.** A scraper is the fastest way to get shut down or sued.

## 3. Tiers & pricing
Pricing anchors: paid decoders cost $5–10 (Reddit), ClassicDecoder $29.99, Marti Deluxe $55, PHS ~$95+.
- **ID Check, $19:** VIN and tag decode, a check of claims against photos (e.g. SS/R-T/GTO badges against the VIN), conflicts flagged, and a matching-numbers checklist.
- **Value Report, $39 (main tier):** everything in ID Check, plus 5–15 sold comps, a low/mid/high value range with a confidence score, and value drivers.
- **Estate/Pro, $49:** everything in the Value Report, plus a human-reviewed PDF, a "how to sell" section, and one follow-up question.
- **Upsells:** Listing Scam Check +$15 (for someone else's ad: VIN/tag consistency, reused photos, price far below market). Restoration Cost Estimate +$19 (rough ranges by condition grade, with clear caveats). Referral to Marti/PHS where it applies.
- Refund automatically if the confidence score is too low to give a range.
- *These prices are my proposal, not market data.* Test $39 against $49 for the main tier.

## 4. Agent workflow
1. **Intake (web form):** year/make/model, VIN, trim/cowl tag photo, build sheet if available, 6–10 guided photos (engine stamp pad, data plate, interior, exterior), and an honest condition questionnaire.
2. **Pay:** Stripe Checkout. A webhook creates the job and nothing runs before payment clears.
3. **Decode agent:** rule tables for each make and era (Chevy, Ford, Mopar, Pontiac, Olds, Buick, AMC, 1955–1990), with a vision model reading the tag and stamps. Outputs the VIN fields, tag fields, a match/conflict matrix, and the source of every rule.
4. **Matching-numbers agent:** compares engine pad, VIN derivative, date codes and casting numbers seen in photos. Grades each item Match / Mismatch / Unverifiable.
5. **Comps agent:** queries the licensed feed, filters by year, trim, engine and transmission, adjusts for condition, and outputs a range plus a list of comps with links.
6. **Confidence gate:** if the decode conflicts, the car is rare or high-value (e.g. range above $75k), photos are unreadable, or there are fewer than 5 comps, the job goes to the **human review queue**: Eric or a paid expert reviewer, with a 24h SLA. Otherwise it's sent automatically.
7. **Report:** HTML template rendered to PDF, with a cover, an ID summary, a matching-numbers table, comps, the range, next steps (e.g. "order a Marti Report") and the disclaimer.
8. **Deliver:** email a signed link. Ask for a review after 3 days and offer upsells.
9. **Log:** keep every prediction and track it against real sales later to calibrate the model.

## 5. MVP tech stack (vibe-coded)
Next.js on Vercel · Supabase (auth, Postgres, photo storage) · Stripe Checkout + webhooks · a vision-capable LLM for tag/stamp OCR and report text · decode tables kept as versioned JSON/YAML · comp feed through a licensed API · Inngest or a queue worker for agent steps · PDF through Playwright HTML→PDF · email through Resend/Postmark · a simple admin page for the review queue · PostHog for analytics.

## 6. Go-to-market (helpful, not spammy)
- **Reddit** (r/musclecar, r/classiccars, r/projectcar, make subs): answer "what is this / what's it worth" posts in full, for free, with a real decode and real comps, and no link unless someone asks. Read each sub's self-promotion rules first. Run one mod-approved "free decode Friday".
- **Forums** (team.net-style make forums, Corvette, Mopar, Pontiac and Ford boards): post free decode cheat sheets with the sources cited. Put the link in your forum signature only where that's allowed.
- **Facebook groups** (model and regional groups): ask admins first, then offer free reports to members.
- **SEO content:** "how to read a 1969 Camaro cowl tag" and "what's my inherited car worth" guides, each one a free decoder that leads into the paid report.
- **Partnerships:** estate attorneys and executors, small classic dealers, and affiliate referrals to Marti/PHS.
- Eric's angle on X: post "AI agent built this report in 3 minutes" before/after threads.

## 7. Risks & mitigations
- **Biggest: valuation liability and data access.** Customers may use the number for insurance, estates, taxes or a sale. The report is **not a certified appraisal**: it isn't USPAP-compliant and the IRS, courts and insurers won't accept it. The data risk is that the best comps (BaT, Mecum) ban scraping, so the business depends on a licensed feed.
- **Wrong decode or "numbers match" verdict:** show the source and confidence for every field, use "Unverifiable" generously, and send unclear cases to human review.
- **Fraud and forged tags:** the PHS founder documents forged tags and build sheets (classicalpontiac.com/restoration/original.html). Never certify authenticity. Recommend factory documentation instead.
- **Chargebacks and refunds:** set clear deliverables up front and refund automatically when confidence is low.
- **Platform bans for promotion:** stick to value-first posting and get mod or admin approval.
- **Disclaimer (put it in every report and at checkout):** *"This report is an informational market estimate based on publicly reported sales and the information and photos you provided. It is not a certified or USPAP-compliant appraisal, an inspection, or a guarantee of authenticity, originality, or value, and must not be relied on for insurance, tax, legal, estate, or lending purposes. Verify with a qualified appraiser and factory documentation (e.g., Marti, PHS). Liability is limited to the price paid."* Have a lawyer review it.

## 8. Two-week MVP checklist
**Week 1**
- [ ] Day 1: email Classic.com data support; check Old Cars Data API terms and pricing; set up Stripe and Supabase accounts
- [ ] Days 1–2: intake form, photo upload, Stripe Checkout and webhook that creates the job
- [ ] Days 2–4: decode tables for the 1964–1974 Chevy/Ford/Mopar/Pontiac core, unit tests against known VINs
- [ ] Days 4–5: vision OCR for the tag and engine pad; match/conflict matrix
- [ ] Days 5–7: comps agent on the licensed or free-permitted feed; range and confidence formula

**Week 2**
- [ ] Days 8–9: PDF template, disclaimer, email delivery
- [ ] Day 10: confidence gate and review-queue admin page
- [ ] Day 11: run 20 free test reports on real Reddit posts (with permission) and compare against known sale prices
- [ ] Day 12: ToS/privacy pages, refund policy, legal review of the disclaimer
- [ ] Day 13: landing page, analytics, first 3 SEO decoder guides
- [ ] Day 14: soft launch to forums and Facebook groups; track conversion, refunds and review rate (goal: under 20% of jobs need human review)
