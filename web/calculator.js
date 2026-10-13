"use strict";

/** Calculate the original Duke Treadmill Score from a standard Bruce test. */
function calculateDukeScore(exerciseMinutes, stDeviationMm, anginaIndex) {
  const raw = [exerciseMinutes, stDeviationMm];
  const names = ["Exercise duration", "ST deviation"];
  const values = raw.map((input, i) => {
    if (input === "" || input === null || input === undefined || typeof input === "boolean") {
      throw new Error(names[i] + " is required.");
    }
    const value = Number(input);
    if (!Number.isFinite(value) || value < 0) {
      throw new Error(names[i] + " must be a finite, non-negative number.");
    }
    return value;
  });
  if (![0, 1, 2, "0", "1", "2"].includes(anginaIndex)) {
    throw new Error("Select a valid angina index (0, 1, or 2).");
  }
  const angina = Number(anginaIndex);
  const score = values[0] - 5 * values[1] - 4 * angina;
  return {
    score,
    tier: score >= 5 ? "Low" : score >= -10 ? "Moderate" : "High",
    exerciseMinutes: values[0],
    stDeviationMm: values[1],
    anginaIndex: angina,
    stPenalty: 5 * values[1],
    anginaPenalty: 4 * angina
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { calculateDukeScore };
}

if (typeof document !== "undefined") {
  const form = document.getElementById("duke-form");
  const scoreText = document.getElementById("score");
  const tierText = document.getElementById("tier");
  const components = document.getElementById("components");
  const message = document.getElementById("message");
  const download = document.getElementById("download");
  let lastResult = null;

  function display(result) {
    scoreText.textContent = result.score.toFixed(2);
    tierText.textContent = result.tier + " risk stratum";
    tierText.dataset.tier = result.tier.toLowerCase();
    components.textContent =
      result.exerciseMinutes.toFixed(2) + " − " +
      result.stPenalty.toFixed(2) + " (ST) − " +
      result.anginaPenalty.toFixed(2) + " (angina)";
    message.textContent = "Calculation completed using the entered exercise-test values.";
    message.className = "message";
    download.disabled = false;
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    try {
      lastResult = calculateDukeScore(
        document.getElementById("exercise_minutes").value,
        document.getElementById("st_deviation_mm").value,
        document.getElementById("angina_index").value
      );
      display(lastResult);
    } catch (error) {
      lastResult = null;
      scoreText.textContent = "—";
      tierText.textContent = "No valid result";
      delete tierText.dataset.tier;
      components.textContent = "Enter valid exercise-test measurements.";
      download.disabled = true;
      message.textContent = error.message;
      message.className = "message error";
    }
  });

  form.addEventListener("reset", () => {
    lastResult = null;
    scoreText.textContent = "—";
    tierText.textContent = "Awaiting input";
    delete tierText.dataset.tier;
    components.textContent = "Exercise minutes − (5 × ST deviation) − (4 × angina index)";
    download.disabled = true;
    message.textContent = "";
    message.className = "message";
  });

  download.addEventListener("click", () => {
    if (!lastResult) return;
    const r = lastResult;
    const csv = "exercise_minutes,st_deviation_mm,angina_index,score,tier\n" +
      [r.exerciseMinutes, r.stDeviationMm, r.anginaIndex, r.score,
        r.tier.toLowerCase()].join(",") + "\n";
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "duke-treadmill-score.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  });
}
