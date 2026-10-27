// node relay/test.mjs: the relay against a fake GitHub (no network)
import assert from "node:assert";
import worker from "./worker.js";
const calls = [];
let existing = 404, found = 0;
globalThis.fetch = async (url, init = {}) => {
  calls.push({ url, init });
  if (url.includes("/contents/")) return new Response("", { status: existing });
  if (url.includes("/search/")) return new Response(JSON.stringify({ total_count: found }), { status: 200 });
  return new Response("{}", { status: 201 });
};
const post = (b) => worker.fetch(new Request("https://r/capture", { method: "POST", body: typeof b === "string" ? b : JSON.stringify(b) }), { GITHUB_TOKEN: "t" });
const p = { schema: "coilofduty.pickup/1", id: "0e7c1d2a-1111-2222-3333-444455556666", brand: "Seymour Duncan", model: "Custom Custom SH-5",
  position: "bridge", context: { tool: "RackNAM", protocol: "capture/1" } };
assert.equal((await post(p)).status, 201);
const issue = JSON.parse(calls.at(-1).init.body);
assert.ok(calls[0].url.endsWith("/pickups/seymour-duncan/custom-custom-sh-5/" + p.id + ".json"));
assert.deepEqual(issue.labels, ["capture"]);
assert.match(issue.body, /```json\n\{[\s\S]*"brand": "Seymour Duncan"[\s\S]*\n```/);
assert.match(issue.body, /- \[X\] I followed/);
assert.equal((await post({ ...p, brand: " " })).status, 422);
assert.equal((await post("nope")).status, 422);
existing = 200; assert.equal((await post(p)).status, 409);
existing = 404; found = 1; assert.equal((await post(p)).status, 409);
console.log("RELAY TEST OK");
