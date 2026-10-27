// pickup-db relay (Cloudflare Worker): RackNAM / Coil of Duty POST a capture to /capture and it becomes a 'Pickup capture'
// issue, which the capture-issue Action turns into a pull request. The relay holds the only write token, so the apps carry
// none. Replies: 201 opened, 409 already in the database or submitted, 422 not a shareable profile, 502 GitHub failed.
// ponytail: no per-IP rate limit; add a Cloudflare rate-limiting rule on /capture if someone spams it.
const REPO = "tlabcustomaudio/pickup-db";
// same as tools/issue_to_file.py slug(), so the duplicate check finds the file the Action would write
const slug = (s) => (s || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60) || "unknown";
const reply = (status, text) => new Response(text + "\n", { status });

export default {
  async fetch(req, env) {
    if (req.method !== "POST" || new URL(req.url).pathname !== "/capture") return reply(404, "POST /capture");
    const text = await req.text();
    if (text.length > 200000) return reply(413, "too big");
    let p;
    try { p = JSON.parse(text); } catch { return reply(422, "not JSON"); }
    if (p?.schema !== "coilofduty.pickup/1" || !/^[0-9a-f-]{36}$/.test(p.id || "") || !String(p.brand || "").trim() || !String(p.model || "").trim())
      return reply(422, "not a shareable coilofduty.pickup/1 profile (brand and model required)");
    const gh = (path, init = {}) => fetch("https://api.github.com" + path, {
      ...init,
      headers: { authorization: `Bearer ${env.GITHUB_TOKEN}`, accept: "application/vnd.github+json", "user-agent": "pickup-db-relay" },
    });
    if ((await gh(`/repos/${REPO}/contents/pickups/${slug(p.brand)}/${slug(p.model)}/${p.id}.json`)).status === 200)
      return reply(409, "already in the database");
    const q = await gh(`/search/issues?q=${encodeURIComponent(`repo:${REPO} is:issue "${p.id}"`)}`);
    if (q.ok && (await q.json()).total_count > 0) return reply(409, "already submitted");
    let json = JSON.stringify(p, null, 1);
    if (json.length > 60000) { delete p.z; json = JSON.stringify(p, null, 1); } // GitHub issue bodies stop at 65536
    const followed = p.context?.protocol === "capture/1" ? "X" : " ";
    const body = "### Profile JSON\n\n```json\n" + json + "\n```\n\n### Protocol\n\n"
      + `- [${followed}] I followed CAPTURE.md (calibrated this session, three scans, no steel near the pickup)\n`
      + "- [X] I agree to publish this capture under CC BY 4.0\n\n### Notes\n\n"
      + `Shared automatically by ${String(p.context?.tool || "Coil of Duty").slice(0, 80)}: its user accepted the sharing notice.\n`;
    const title = `Capture: ${p.brand} ${p.model} (${p.position})`.slice(0, 200);
    const r = await gh(`/repos/${REPO}/issues`, { method: "POST", body: JSON.stringify({ title, body, labels: ["capture"] }) });
    return r.ok ? reply(201, "ok") : reply(502, "github " + r.status);
  },
};
