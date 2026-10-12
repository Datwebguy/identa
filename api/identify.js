// Read-only check of one company domain. It calls Crustdata's identify endpoint (free) and
// applies the same acceptance rule as the agent. It writes nothing: no GitHub call, no save.
// The Crustdata key comes from the CRUSTDATA_API_KEY environment variable and is never returned.

const THRESHOLD = 0.9; // the same value as confidence_threshold in identa.toml
const BASE_URL = "https://api.crustdata.com";
const API_VERSION = "2025-11-01";
const DOMAIN = /^(?=.{4,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,24}$/;

// Best-effort limits kept in memory. Each server instance has its own counters.
const PER_IP_LIMIT = 5;
const GLOBAL_LIMIT = 20;
const WINDOW_MS = 60 * 1000;
const hits = new Map();
let globalHits = [];

function allowed(ip, now) {
  globalHits = globalHits.filter((t) => now - t < WINDOW_MS);
  const mine = (hits.get(ip) || []).filter((t) => now - t < WINDOW_MS);
  if (globalHits.length >= GLOBAL_LIMIT || mine.length >= PER_IP_LIMIT) return false;
  mine.push(now);
  globalHits.push(now);
  hits.set(ip, mine);
  if (hits.size > 1000) hits.clear();
  return true;
}

// The same rule as decide_identity in src/identa/workflow.py.
function decide(matches) {
  if (!matches.length) return { decision: "hold", reason: "no match" };
  const top = matches[0];
  const score = Number(top.confidence_score);
  const tied = matches.filter((m) => m.confidence_score === top.confidence_score);
  const name = (top.company_data.basic_info || {}).name || null;
  const base = {
    name,
    company_id: top.company_data.crustdata_company_id,
    confidence: score,
  };
  if (score < THRESHOLD) return { ...base, decision: "hold", reason: "confidence below threshold" };
  if (tied.length > 1) {
    return {
      ...base,
      decision: "hold",
      reason: "tie at top confidence",
      candidates: tied.map((m) => ({
        company_id: m.company_data.crustdata_company_id,
        name: (m.company_data.basic_info || {}).name || null,
        confidence: Number(m.confidence_score),
      })),
    };
  }
  return { ...base, decision: "accept", reason: "one match at or above the threshold" };
}

async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("Content-Type", "application/json");
  const send = (code, body) => res.status(code).send(JSON.stringify(body));
  if (req.method !== "GET") return send(405, { error: "Use GET." });
  const key = process.env.CRUSTDATA_API_KEY;
  if (!key) return send(503, { error: "The live check is not switched on." });
  const domain = String((req.query || {}).domain || "").trim().toLowerCase();
  if (!DOMAIN.test(domain)) return send(400, { error: "Enter a domain such as example.com." });
  const ip = String(req.headers["x-forwarded-for"] || "unknown").split(",")[0].trim();
  if (!allowed(ip, Date.now())) return send(429, { error: "Too many checks. Try again in a minute." });
  try {
    const resp = await fetch(BASE_URL + "/company/identify", {
      method: "POST",
      headers: {
        Authorization: "Bearer " + key,
        "x-api-version": API_VERSION,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ domains: [domain], exact_match: true }),
      signal: AbortSignal.timeout(15000),
    });
    if (resp.status === 404) return send(200, { domain, ...decide([]) });
    if (resp.status !== 200) return send(502, { error: "The lookup service did not answer." });
    const entries = await resp.json();
    return send(200, { domain, ...decide((entries[0] || {}).matches || []) });
  } catch (err) {
    return send(502, { error: "The lookup service did not answer." });
  }
}

module.exports = handler;
module.exports.decide = decide;
