const EMAIL_RE = /^[^\s@<>()[\]\\,;:"]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$/;
const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { "content-type": "application/json", "cache-control": "no-store" } });
async function syncToResend(env, email) {
  if (!env.RESEND_API_KEY || !env.RESEND_SEGMENT_ID) return false;
  const h = { authorization: "Bearer " + env.RESEND_API_KEY, "content-type": "application/json" };
  try {
    const r = await fetch("https://api.resend.com/contacts", { method: "POST", headers: h, body: JSON.stringify({ email, unsubscribed: false, segments: [{ id: env.RESEND_SEGMENT_ID }] }) });
    if (r.ok) return true;
    // contact may already exist: just add it to the segment
    const s = await fetch("https://api.resend.com/contacts/" + encodeURIComponent(email) + "/segments/" + env.RESEND_SEGMENT_ID, { method: "POST", headers: h });
    return s.ok;
  } catch { return false; }
}
async function onRequestPost({ request, env, ctx }) {
  let form;
  try { form = await request.formData(); } catch { return json({ ok: false, error: "Invalid form submission." }, 400); }
  if ((form.get("website") || "").toString().trim() !== "") return json({ ok: true }); // honeypot: silently drop bots
  const email = (form.get("email") || "").toString().trim().toLowerCase();
  const car = (form.get("car") || "").toString().trim().slice(0, 120);
  if (email.length > 254 || !EMAIL_RE.test(email)) return json({ ok: false, error: "Please enter a valid email address." }, 400);
  const key = "email:" + email;
  if (!(await env.WAITLIST.get(key))) {
    const rec = { email, car, ts: new Date().toISOString(), country: request.cf?.country || null };
    await env.WAITLIST.put(key, JSON.stringify(rec)); // KV stays the source of truth
    const job = syncToResend(env, email).then(ok => ok ? env.WAITLIST.put(key, JSON.stringify({ ...rec, resend: true })) : null);
    if (ctx?.waitUntil) ctx.waitUntil(job); else await job;
  }
  return json({ ok: true });
}
const methodNotAllowed = () => json({ ok: false, error: "Method not allowed" }, 405);

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/api/waitlist") {
      return request.method === "POST" ? onRequestPost({ request, env, ctx }) : methodNotAllowed();
    }
    return env.ASSETS.fetch(request);
  }
};
