// Pure-function checks of the acceptance rule. Run: node --test tests/identify.test.js
const test = require("node:test");
const assert = require("node:assert");
const { decide } = require("../api/identify.js");

const m = (id, name, score) => ({
  confidence_score: score,
  company_data: { crustdata_company_id: id, basic_info: { name } },
});

test("no match is held", () => {
  assert.strictEqual(decide([]).reason, "no match");
});
test("below the threshold is held", () => {
  assert.strictEqual(decide([m(1, "a", 0.5)]).reason, "confidence below threshold");
});
test("a tie at the top is held with its candidates", () => {
  const r = decide([m(1, "a", 1), m(2, "b", 1)]);
  assert.strictEqual(r.reason, "tie at top confidence");
  assert.strictEqual(r.candidates.length, 2);
});
test("one match at or above the threshold is accepted", () => {
  assert.strictEqual(decide([m(1, "a", 0.9)]).decision, "accept");
  assert.strictEqual(decide([m(1, "a", 1), m(2, "b", 0.4)]).decision, "accept");
});
