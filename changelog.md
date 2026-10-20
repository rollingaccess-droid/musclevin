# MuscleVIN changelog

What changed on musclevin.com and why. Newest first.

## 2026-10-20 · Weekly growth sprint 1: search and AI-assistant discoverability

**Starting point.** Waitlist signups in KV: 0 (checked 10:05 AM ET). With no traffic there is nothing to A/B test yet, so this sprint went to getting found rather than conversion copy. The site had no robots.txt, no sitemap, no llms.txt, no canonical URL, and only one page.

**Changed**
- Added `robots.txt` (allow all, disallow `/api/`, points to the sitemap) and `sitemap.xml` (home page plus the new guide). Without these, crawlers had nothing to discover beyond the home page.
- Added `llms.txt`, a plain summary for AI assistants: what the decoder covers, what a VIN can't prove, the not-an-appraisal line, and links to the tool, sample, guide, and FAQ. Reports are described as not on sale yet; no prices or stats were added.
- Added the first helpful-content page, `/guides/1969-chevelle-vin` ("How to decode a 1969 Chevelle VIN"). Every code table comes from the two chevellestuff.net pages already cited as S1 and S2 in `app/README.md`, both re-read on Oct 20. It has TechArticle and BreadcrumbList structured data with the sources listed as citations. Where the two sources disagree (series 31/32: Nomad vs Chevelle 300), the page shows both instead of picking one.
- Home page: added a canonical link and `og:url`, linked the guide from the footer, and removed a stale "placeholder endpoint" HTML comment (the waitlist endpoint has been live since Oct 15).
- Worker routing: clean URLs now serve `<path>.html`, and a request for `/guides/....html` 301-redirects to the clean URL so there's one canonical address per page. All other routes are unchanged, including the waitlist handler.
- `deploy/build_inline_worker.py` now embeds the four new files.

**Found, not fixed yet.** The decoder's 1965-71 Chevrolet series table labels 1969 series 31/32 as "Chevelle 300". chevellestuff.net's 1969 VIN page says Nomad and its Protect-O-Plate page says Chevelle 300. The decoder output should note the disagreement for 1969. That's a decoder-data change (Python and JS tables plus tests), so it's queued for a later sprint.

**Next sprint candidates**
- Submit the sitemap in Google Search Console and Bing Webmaster Tools. Both are free, but need Eric's Google or Microsoft sign-in to verify the domain.
- Free Cloudflare Web Analytics so there's a traffic baseline to measure signups against.
- More per-model guides from the cited sources: 1969 Camaro (S8), 1965-71 GTO (S5, S7), 1969 Mopar B-body (S12, S15, S18), 1965-73 Mustang (S9).
- Monetization check: waitlist is at 0, well below the ~50 threshold, and the comps data license isn't secured, so no paid-report proposal this week.

**Safety.** Backup before deploy: `backups/pre-seo-sprint-20261020` (rollback target: production deployment a6b46049).
