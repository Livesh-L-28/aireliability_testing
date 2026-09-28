// AI Reliability Studio Frontend Logic

document.addEventListener("DOMContentLoaded", () => {
  const btnRunEval = document.getElementById("btnRunEval");
  const btnQuickCompare = document.getElementById("btnQuickCompare");
  const btnCloseCompare = document.getElementById("btnCloseCompare");
  const compareSection = document.getElementById("compareSection");
  const orderIdInput = document.getElementById("orderIdInput");
  const labelCorrect = document.getElementById("labelCorrect");
  const labelBroken = document.getElementById("labelBroken");
  const loadingIndicator = document.getElementById("loadingIndicator");
  const resultsSection = document.getElementById("resultsSection");
  const btnToggleRaw = document.getElementById("btnToggleRaw");
  const rawTraceJson = document.getElementById("rawTraceJson");

  // Radio button styling toggle
  document.querySelectorAll('input[name="agentType"]').forEach((radio) => {
    radio.addEventListener("change", (e) => {
      if (e.target.value === "correct") {
        labelCorrect.classList.add("active");
        labelBroken.classList.remove("active");
      } else {
        labelBroken.classList.add("active");
        labelCorrect.classList.remove("active");
      }
    });
  });

  // Toggle raw JSON trace
  btnToggleRaw.addEventListener("click", () => {
    rawTraceJson.classList.toggle("hidden");
    btnToggleRaw.textContent = rawTraceJson.classList.contains("hidden")
      ? "View JSON ExecutionTrace"
      : "Hide JSON ExecutionTrace";
  });

  // Quick Compare toggle
  btnQuickCompare.addEventListener("click", () => {
    compareSection.classList.remove("hidden");
    compareSection.scrollIntoView({ behavior: "smooth" });
  });

  btnCloseCompare.addEventListener("click", () => {
    compareSection.classList.add("hidden");
  });

  // Run Evaluation click handler
  btnRunEval.addEventListener("click", async () => {
    const orderId = orderIdInput.value.trim() || "ORD-1001";
    const selectedAgent = document.querySelector('input[name="agentType"]:checked').value;

    loadingIndicator.classList.remove("hidden");
    resultsSection.classList.add("hidden");

    try {
      const response = await fetch("/api/run-evaluation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          order_id: orderId,
          agent_type: selectedAgent,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const data = await response.json();
      renderResults(data);
    } catch (err) {
      alert("Evaluation failed: " + err.message);
    } finally {
      loadingIndicator.classList.add("hidden");
    }
  });

  function renderResults(data) {
    resultsSection.classList.remove("hidden");

    // Left card: Agent Execution
    const agentBadge = document.getElementById("agentTypeBadge");
    if (data.agent_type === "correct") {
      agentBadge.textContent = "Compliant";
      agentBadge.className = "badge badge-success";
    } else {
      agentBadge.textContent = "Regression Bug";
      agentBadge.className = "badge badge-danger";
    }

    document.getElementById("resTraceId").textContent = data.trace_id;
    document.getElementById("resAgentOutput").textContent = `"${data.agent_output}"`;

    // Render Steps Timeline
    const timeline = document.getElementById("stepsTimeline");
    timeline.innerHTML = "";

    data.steps.forEach((step) => {
      const stepEl = document.createElement("div");
      stepEl.className = "step-item";
      stepEl.innerHTML = `
        <div class="step-badge">${step.step_num}</div>
        <div class="step-body">
          <div class="step-name">${step.name}(order_id="${data.order_id}")</div>
          <div class="step-meta">Type: ${step.type} • Result: ${JSON.stringify(step.output)}</div>
        </div>
      `;
      timeline.appendChild(stepEl);
    });

    // Populate Raw JSON
    rawTraceJson.textContent = JSON.stringify(data, null, 2);

    // Right card: Reliability Invariant
    const evalBadge = document.getElementById("evalStatusBadge");
    const invVerdict = document.getElementById("invVerdict");
    const failureCard = document.getElementById("failureCard");
    const regressionCard = document.getElementById("regressionCard");
    const passCard = document.getElementById("passCard");

    if (data.evaluation.passed) {
      evalBadge.textContent = "PASSED";
      evalBadge.className = "badge badge-success";
      invVerdict.innerHTML = `<span style="color:#34d399">✔ Invariant Satisfied: check_order executed before refund_order</span>`;

      passCard.classList.remove("hidden");
      failureCard.classList.add("hidden");
      regressionCard.classList.add("hidden");
    } else {
      evalBadge.textContent = "FAILED";
      evalBadge.className = "badge badge-danger";
      invVerdict.innerHTML = `<span style="color:#f87171">✖ Invariant Violated: Tool sequence out of order!</span>`;

      passCard.classList.add("hidden");
      failureCard.classList.remove("hidden");

      // Failure Details
      document.getElementById("failCategoryBadge").textContent = (data.failure_report.category || "TOOL").toUpperCase();
      document.getElementById("failReason").textContent = data.failure_report.reason.split("\n")[0];
      document.getElementById("diffExpected").textContent = data.evaluation.expected_order.join(" ➔ ");
      document.getElementById("diffActual").textContent = data.evaluation.actual_order.join(" ➔ ");

      // Regression Test Details
      if (data.regression_test) {
        regressionCard.classList.remove("hidden");
        document.getElementById("regId").textContent = data.regression_test.id;
        document.getElementById("regSourceFail").textContent = data.regression_test.source_failure_id;
      }
    }

    resultsSection.scrollIntoView({ behavior: "smooth" });
  }

  // Auto-run once on load for immediate satisfaction
  btnRunEval.click();
});
