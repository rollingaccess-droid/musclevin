const EMAIL_RE = /^[^\s@<>()[\]\\,;:"]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$/;
const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { "content-type": "application/json", "cache-control": "no-store" } });
export async function onRequestPost({ request, env }) {
  let form;
  try { form = await request.formData(); } catch { return json({ ok: false, error: "Invalid form submission." }, 400); }
  if ((form.get("website") || "").toString().trim() !== "") return json({ ok: true }); // honeypot: silently drop bots
  const email = (form.get("email") || "").toString().trim().toLowerCase();
  const car = (form.get("car") || "").toString().trim().slice(0, 120);
  if (email.length > 254 || !EMAIL_RE.test(email)) return json({ ok: false, error: "Please enter a valid email address." }, 400);
  const key = "email:" + email;
  if (!(await env.WAITLIST.get(key))) {
    await env.WAITLIST.put(key, JSON.stringify({ email, car, ts: new Date().toISOString(), country: request.cf?.country || null }));
  }
  return json({ ok: true });
}
export const onRequest = () => json({ ok: false, error: "Method not allowed" }, 405);
