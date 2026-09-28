// AI Reliability Studio Frontend Logic v3.0

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const scenarioCards = document.querySelectorAll(".sc-card");
  const scenarioSummaryDesc = document.getElementById("scenarioSummaryDesc");
  const inputLabelText = document.getElementById("inputLabelText");
  const scenarioInput = document.getElementById("scenarioInput");
  const correctFlowDesc = document.getElementById("correctFlowDesc");
  const brokenFlowDesc = document.getElementById("brokenFlowDesc");

  const btnRunEval = document.getElementById("btnRunEval");
  const btnQuickCompare = document.getElementById("btnQuickCompare");
  const btnCloseCompare = document.getElementById("btnCloseCompare");
  const btnSimulateCI = document.getElementById("btnSimulateCI");
  const btnCloseCI = document.getElementById("btnCloseCI");
  const compareSection = document.getElementById("compareSection");
  const ciSection = document.getElementById("ciSection");
  const labelCorrect = document.getElementById("labelCorrect");
  const labelBroken = document.getElementById("labelBroken");
  const loadingIndicator = document.getElementById("loadingIndicator");
  const resultsSection = document.getElementById("resultsSection");
  const btnToggleRaw = document.getElementById("btnToggleRaw");
  const btnCopyJson = document.getElementById("btnCopyJson");
  const rawTraceJson = document.getElementById("rawTraceJson");

  // State
  let selectedScenario = "refund";
  let currentEvaluationData = null;

  const scenarioMeta = {
    refund: {
      title: "Customer Refund Agent",
      label: "Order ID Under Test",
      defaultInput: "ORD-1001",
      tool1: "check_order",
      tool2: "refund_order",
      desc1: "Eligibility check",
      desc2: "Financial refund",
    },
    admin: {
      title: "Admin Account Upgrade Agent",
      label: "User / Account ID Under Test",
      defaultInput: "USR-8821",
      tool1: "authenticate_admin",
      tool2: "update_account",
      desc1: "MFA Authentication",
      desc2: "Privilege update",
    },
    wire: {
      title: "Bank Wire Transfer Agent",
      label: "Customer ID Under Test",
      defaultInput: "CUST-902",
      tool1: "verify_kyc",
      tool2: "execute_wire_transfer",
      desc1: "KYC Compliance check",
      desc2: "Disburse money wire",
    },
    cancel: {
      title: "Order Cancellation Agent",
      label: "Order ID Under Test",
      defaultInput: "ORD-5544",
      tool1: "lookup_order",
      tool2: "cancel_order",
      desc1: "Shipment lookup",
      desc2: "Inventory cancel",
    },
  };

  // Scenario Card Click Listener
  scenarioCards.forEach((card) => {
    card.addEventListener("click", () => {
      scenarioCards.forEach((c) => c.classList.remove("active"));
      card.classList.add("active");

      selectedScenario = card.getAttribute("data-scenario");
      updateScenarioUI(selectedScenario);
      btnRunEval.click();
    });
  });

  function updateScenarioUI(scKey) {
    const meta = scenarioMeta[scKey] || scenarioMeta.refund;
    scenarioSummaryDesc.textContent = `Currently testing: ${meta.title}`;
    inputLabelText.textContent = meta.label;
    scenarioInput.value = meta.defaultInput;

    correctFlowDesc.innerHTML = `<code>${meta.tool1}</code> ➔ <code>${meta.tool2}</code>`;
    brokenFlowDesc.innerHTML = `<code>${meta.tool2}</code> ➔ <code>${meta.tool1}</code>`;
  }

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

  // Copy raw JSON to clipboard
  btnCopyJson.addEventListener("click", () => {
    if (rawTraceJson.textContent) {
      navigator.clipboard.writeText(rawTraceJson.textContent).then(() => {
        const orig = btnCopyJson.textContent;
        btnCopyJson.textContent = "✔ Copied!";
        setTimeout(() => { btnCopyJson.textContent = orig; }, 1800);
      });
    }
  });

  // Quick Compare toggle
  btnQuickCompare.addEventListener("click", () => {
    compareSection.classList.remove("hidden");
    renderComparisonVisualizer();
    compareSection.scrollIntoView({ behavior: "smooth" });
  });

  btnCloseCompare.addEventListener("click", () => {
    compareSection.classList.add("hidden");
  });

  function renderComparisonVisualizer() {
    const meta = scenarioMeta[selectedScenario] || scenarioMeta.refund;
    const passVis = document.getElementById("comparePassVis");
    const failVis = document.getElementById("compareFailVis");
    const passOut = document.getElementById("comparePassOut");
    const failOut = document.getElementById("compareFailOut");

    passVis.innerHTML = `
      <div class="step-card step-ok">1. ${meta.tool1} (${meta.desc1})</div>
      <div class="step-arrow">↓</div>
      <div class="step-card step-ok">2. ${meta.tool2} (${meta.desc2})</div>
    `;

    failVis.innerHTML = `
      <div class="step-card step-err">1. ${meta.tool2} (EXECUTED PREMATURELY!)</div>
      <div class="step-arrow">↓</div>
      <div class="step-card step-warn">2. ${meta.tool1} (Validated too late)</div>
    `;

    const sampleOut = currentEvaluationData ? currentEvaluationData.agent_output : "Workflow finished successfully";
    passOut.textContent = `Output: "${sampleOut}"`;
    failOut.textContent = `Output: "${sampleOut}"`;
  }

  // CI Pipeline Simulator
  btnSimulateCI.addEventListener("click", () => {
    ciSection.classList.remove("hidden");
    ciSection.scrollIntoView({ behavior: "smooth" });
    runCiSimulation();
  });

  btnCloseCI.addEventListener("click", () => {
    ciSection.classList.add("hidden");
  });

  function runCiSimulation() {
    const ciStep3 = document.getElementById("ciInvariantStatus");
    const ciDeploy = document.getElementById("ciDeployStatus");
    const logBox = document.getElementById("ciLogBox");
    const meta = scenarioMeta[selectedScenario] || scenarioMeta.refund;

    ciStep3.textContent = "Evaluating invariants...";
    ciStep3.className = "ci-step-status pending";
    ciDeploy.textContent = "Evaluating...";
    ciDeploy.className = "ci-step-status pending";

    logBox.textContent = `[CI] Initializing runner for scenario: ${meta.title}...\n[CI] Step 1: Flake8 & Ruff linting passed.\n[CI] Step 2: Pytest unit tests passed (3/3 functions).\n[CI] Step 3: Invoking aireliability regression invariants...\n`;

    setTimeout(() => {
      const isCompliant = currentEvaluationData && currentEvaluationData.agent_type === "correct";

      if (isCompliant) {
        ciStep3.textContent = "Passed (6/6 Invariants)";
        ciStep3.className = "ci-step-status ok";
        ciDeploy.textContent = "Deployment Approved ✔";
        ciDeploy.className = "ci-step-status ok";

        logBox.textContent += `[CI] ✔ Invariant '${meta.tool1} -> ${meta.tool2}' PASSED.\n` +
          "[CI] ✔ Safety policy 'no destructive tools' PASSED.\n" +
          "[CI] ✔ SLA Latency constraint PASSED (<1000ms).\n" +
          "[CI] SUCCESS: Build certified reliable. Triggering production CD rollout!\n";
      } else {
        ciStep3.textContent = "Failed (Invariant Broken)";
        ciStep3.className = "ci-step-status fail";
        ciDeploy.textContent = "Deployment BLOCKED 🛑";
        ciDeploy.className = "ci-step-status fail";

        logBox.textContent += `[CI] ✖ CRITICAL FAILURE: Invariant '${meta.tool1} -> ${meta.tool2}' VIOLATED!\n` +
          `[CI] ✖ Tool '${meta.tool2}' executed before prerequisite '${meta.tool1}'.\n` +
          `[CI] 🛡️ RegressionGenerator active: synthesized test case 'reg_${selectedScenario}_violation'.\n` +
          "[CI] BLOCKED: Release halted by aireliability gatekeeper. PR cannot be merged!\n";
      }
    }, 900);
  }

  // Run Evaluation click handler
  btnRunEval.addEventListener("click", async () => {
    const paramVal = scenarioInput.value.trim() || scenarioMeta[selectedScenario].defaultInput;
    const selectedAgent = document.querySelector('input[name="agentType"]:checked').value;

    loadingIndicator.classList.remove("hidden");
    resultsSection.classList.add("hidden");

    try {
      const response = await fetch("/api/run-evaluation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario: selectedScenario,
          param: paramVal,
          agent_type: selectedAgent,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const data = await response.json();
      currentEvaluationData = data;
      renderResults(data);
    } catch (err) {
      alert("Evaluation failed: " + err.message);
    } finally {
      loadingIndicator.classList.add("hidden");
    }
  });

  function renderResults(data) {
    resultsSection.classList.remove("hidden");

    // Update KPI Bar
    const kpiPassRate = document.getElementById("kpiPassRate");
    const kpiPassSub = document.getElementById("kpiPassSub");
    const kpiLatency = document.getElementById("kpiLatency");
    const kpiToolCount = document.getElementById("kpiToolCount");
    const kpiRegStatus = document.getElementById("kpiRegressionStatus");
    const kpiRegSub = document.getElementById("kpiRegressionSub");

    kpiPassRate.textContent = `${data.suite_summary.pass_rate}%`;
    kpiPassRate.style.color = data.evaluation.passed ? "#34d399" : "#f87171";
    kpiPassSub.textContent = `${data.suite_summary.passed} of ${data.suite_summary.total} Invariants Passing`;
    kpiLatency.textContent = `${data.latency_ms || 1.2} ms`;
    kpiToolCount.textContent = `${data.steps.length} Steps`;

    if (data.evaluation.passed) {
      kpiRegStatus.textContent = "Shield Ready";
      kpiRegStatus.style.color = "#34d399";
      kpiRegSub.textContent = "Zero Invariant Flaws";
    } else {
      kpiRegStatus.textContent = "Triggered";
      kpiRegStatus.style.color = "#fbbf24";
      kpiRegSub.textContent = "Regression Test Synthesized";
    }

    // Left Card: Agent Execution
    const agentBadge = document.getElementById("agentTypeBadge");
    if (data.agent_type === "correct") {
      agentBadge.textContent = "Compliant";
      agentBadge.className = "badge badge-success";
    } else {
      agentBadge.textContent = "Regression Bug";
      agentBadge.className = "badge badge-danger";
    }

    document.getElementById("resScenarioTitle").textContent = data.scenario_title;
    document.getElementById("resTraceId").textContent = data.trace_id;
    document.getElementById("resAgentOutput").textContent = `"${data.agent_output}"`;
    document.getElementById("resLatency").textContent = `${data.latency_ms || 1.2} ms`;

    // Render Steps Timeline
    const timeline = document.getElementById("stepsTimeline");
    timeline.innerHTML = "";

    data.steps.forEach((step) => {
      const stepEl = document.createElement("div");
      stepEl.className = "step-item";
      stepEl.innerHTML = `
        <div class="step-badge">${step.step_num}</div>
        <div class="step-body">
          <div class="step-name">${step.name}(param="${data.param_val}")</div>
          <div class="step-meta">Type: ${step.type} • Result: ${JSON.stringify(step.output)}</div>
        </div>
      `;
      timeline.appendChild(stepEl);
    });

    // Populate Raw JSON
    rawTraceJson.textContent = JSON.stringify(data.raw_trace || data, null, 2);

    // Populate Invariants Table
    const tableBody = document.getElementById("invariantsTableBody");
    tableBody.innerHTML = "";

    data.suite_results.forEach((inv) => {
      const tr = document.createElement("tr");
      const statusBadge = inv.passed
        ? `<span class="badge badge-success">PASS</span>`
        : `<span class="badge badge-danger">FAIL</span>`;
      
      tr.innerHTML = `
        <td>
          <div style="font-weight:600; color: ${inv.passed ? '#f3f4f6' : '#fca5a5'};">${inv.name}</div>
          <div style="font-size:0.75rem; color:var(--text-muted);">${inv.description}</div>
        </td>
        <td><span class="inv-cat-pill">${inv.category}</span></td>
        <td>${statusBadge}</td>
      `;
      tableBody.appendChild(tr);
    });

    // Right Card: Invariant Overall Status
    const evalBadge = document.getElementById("evalStatusBadge");
    const failureCard = document.getElementById("failureCard");
    const regressionCard = document.getElementById("regressionCard");
    const passCard = document.getElementById("passCard");
    const passCardDesc = document.getElementById("passCardDesc");

    if (data.evaluation.passed) {
      evalBadge.textContent = "SUITE PASSED";
      evalBadge.className = "badge badge-success";
      passCardDesc.textContent = `All prerequisites verified before initiating side-effects in ${data.scenario_title}. Invariant sequence, safety, presence, and latency verified.`;

      passCard.classList.remove("hidden");
      failureCard.classList.add("hidden");
      regressionCard.classList.add("hidden");
    } else {
      evalBadge.textContent = "SUITE FAILED";
      evalBadge.className = "badge badge-danger";

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
        document.getElementById("regTargetCase").textContent = data.regression_test.target_test_case;
        document.getElementById("regLockedContract").textContent = data.regression_test.required_invariant;
      }
    }

    resultsSection.scrollIntoView({ behavior: "smooth" });
  }

  // Initialize with default scenario
  updateScenarioUI("refund");
  btnRunEval.click();
});
