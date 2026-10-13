"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { calculateDukeScore } = require("./calculator.js");

test("reference formula and representative strata", () => {
  assert.equal(calculateDukeScore(12, 0, 0).score, 12);
  assert.equal(calculateDukeScore(9, 1, 1).score, 0);
  assert.equal(calculateDukeScore(4, 2, 2).score, -14);
  assert.equal(calculateDukeScore(4, 2, 2).tier, "High");
});
test("continuous cut points are classified correctly", () => {
  assert.equal(calculateDukeScore(5, 0, 0).tier, "Low");
  assert.equal(calculateDukeScore(4.99, 0, 0).tier, "Moderate");
  assert.equal(calculateDukeScore(0, 2, 0).tier, "Moderate");
  assert.equal(calculateDukeScore(0, 2.002, 0).tier, "High");
});
test("validation rejects missing, negative, nonfinite and invalid angina values", () => {
  for (const args of [
    ["", 0, 0], [null, 0, 0], [-1, 0, 0],
    [1, -1, 0], [Infinity, 0, 0], [NaN, 0, 0],
    [1, 0, 3], [1, 0, true], [1, 0, ""]
  ]) {
    assert.throws(() => calculateDukeScore(...args));
  }
});
