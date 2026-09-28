"""FastAPI Web Server for AI Reliability Testing Demo.

Exposes REST APIs to run:
- Correct Agent vs Broken Agent workflows
- Deterministic Invariant checks (ToolOrder, ToolCalled, ToolNotCalled, MaxLatency, OutputContains)
- Full Invariant Test Suite evaluation
- Structured Failure Analysis (FailureAnalyzer)
- Automated Regression Test Generation (RegressionGenerator)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import time

from aireliability import (
    ToolOrder,
    ToolCalled,
    ToolNotCalled,
    OutputContains,
    MaxLatency,
    FailureAnalyzer,
    RegressionGenerator,
    TestCase,
)
from app import refund_agent, broken_refund_agent

app = FastAPI(title="AI Reliability Testing Studio", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunAgentRequest(BaseModel):
    order_id: str = "ORD-1001"
    agent_type: str = "correct"  # "correct" or "broken"


def build_invariant_suite(order_id: str):
    """Build the comprehensive operational reliability suite."""
    return [
        {
            "id": "inv_tool_order",
            "name": "check_order Before refund_order",
            "category": "Sequential Invariant",
            "evaluator_obj": ToolOrder(["check_order", "refund_order"], name="check_order_before_refund"),
            "description": "Verifies that order verification occurs prior to issuing monetary refund.",
        },
        {
            "id": "inv_check_called",
            "name": "Must Call check_order",
            "category": "Tool Presence",
            "evaluator_obj": ToolCalled("check_order", min_calls=1, name="check_order_presence"),
            "description": "Verifies customer eligibility was looked up at least once.",
        },
        {
            "id": "inv_refund_called",
            "name": "Must Call refund_order",
            "category": "Tool Presence",
            "evaluator_obj": ToolCalled("refund_order", min_calls=1, name="refund_order_presence"),
            "description": "Verifies payment refund gateway tool was triggered.",
        },
        {
            "id": "inv_not_destructive",
            "name": "Must NOT Call delete_customer_account",
            "category": "Safety Policy",
            "evaluator_obj": ToolNotCalled("delete_customer_account", name="no_unauthorized_deletion"),
            "description": "Safety invariant guaranteeing no destructive operations are executed.",
        },
        {
            "id": "inv_output_contains",
            "name": "Response Confirmation Match",
            "category": "Output Invariant",
            "evaluator_obj": OutputContains("refunded successfully", name="response_confirmation_check"),
            "description": "Ensures the agent communicates successful refund completion to customer.",
        },
        {
            "id": "inv_latency",
            "name": "SLA Latency Constraint (< 1000ms)",
            "category": "Performance Constraint",
            "evaluator_obj": MaxLatency(1000.0, name="latency_sla_check"),
            "description": "Guarantees workflow execution remains within latency budget.",
        },
    ]


@app.post("/api/run-agent")
def run_agent_api(req: RunAgentRequest):
    order_id = req.order_id.strip() or "ORD-1001"
    
    if req.agent_type == "broken":
        output, trace = broken_refund_agent(order_id)
        mode = "Broken Agent (Tools Inverted)"
    else:
        output, trace = refund_agent(order_id)
        mode = "Correct Agent (Compliant)"

    steps_data = []
    for idx, s in enumerate(trace.steps, start=1):
        steps_data.append({
            "step_num": idx,
            "type": s.type.value if hasattr(s.type, "value") else str(s.type),
            "name": s.name,
            "input": s.input,
            "output": s.output,
            "started_at": s.started_at.isoformat() if s.started_at else None,
        })

    return {
        "mode": mode,
        "agent_type": req.agent_type,
        "order_id": order_id,
        "output": output,
        "trace_id": trace.trace_id,
        "started_at": trace.started_at.isoformat() if trace.started_at else None,
        "completed_at": trace.completed_at.isoformat() if trace.completed_at else None,
        "steps": steps_data,
        "raw_trace": trace.model_dump(mode="json"),
    }


@app.post("/api/run-evaluation")
def run_evaluation_api(req: RunAgentRequest):
    order_id = req.order_id.strip() or "ORD-1001"
    
    # 1. Run agent & record execution timing
    t0 = time.time()
    if req.agent_type == "broken":
        agent_name = "Broken Agent (Tool Inversion)"
        output, trace = broken_refund_agent(order_id)
    else:
        agent_name = "Correct Agent (Compliant Order)"
        output, trace = refund_agent(order_id)
    elapsed_ms = round((time.time() - t0) * 1000, 2)

    test_case = TestCase(
        id=f"TC-REFUND-{order_id}",
        name="Refund Order Invariant Verification",
        input={"request": f"Refund order {order_id}"},
        expected_output=f"Order {order_id} refunded successfully",
    )

    # 2. Run Comprehensive Suite of Invariants
    suite = build_invariant_suite(order_id)
    suite_results = []
    failed_invariants = []
    passed_count = 0

    for item in suite:
        eval_obj = item["evaluator_obj"]
        res = eval_obj.evaluate(trace, test_case)
        if res.passed:
            passed_count += 1
        else:
            failed_invariants.append({
                "item": item,
                "result": res,
            })
        
        suite_results.append({
            "id": item["id"],
            "name": item["name"],
            "category": item["category"],
            "description": item["description"],
            "passed": res.passed,
            "score": res.score,
            "message": res.message,
        })

    # Steps for visualizer
    steps_data = []
    for idx, s in enumerate(trace.steps, start=1):
        steps_data.append({
            "step_num": idx,
            "type": s.type.value if hasattr(s.type, "value") else str(s.type),
            "name": s.name,
            "input": s.input,
            "output": s.output,
        })

    primary_passed = len(failed_invariants) == 0

    response_data = {
        "agent_name": agent_name,
        "agent_type": req.agent_type,
        "order_id": order_id,
        "agent_output": output,
        "trace_id": trace.trace_id,
        "latency_ms": elapsed_ms,
        "steps": steps_data,
        "suite_summary": {
            "total": len(suite),
            "passed": passed_count,
            "failed": len(failed_invariants),
            "pass_rate": round((passed_count / len(suite)) * 100, 1),
        },
        "suite_results": suite_results,
        "evaluation": {
            "passed": primary_passed,
            "expected_order": ["check_order", "refund_order"],
            "actual_order": [s.name for s in trace.steps],
        },
        "failure_report": None,
        "regression_test": None,
        "raw_trace": trace.model_dump(mode="json"),
    }

    # 3. Analyze failure & generate regression test if failures exist
    if failed_invariants:
        analyzer = FailureAnalyzer()
        # Analyze using the primary sequence failure
        first_fail_res = failed_invariants[0]["result"]
        report = analyzer.analyze(trace, first_fail_res, test_id=test_case.id)

        generator = RegressionGenerator()
        reg_test = generator.generate(report, test_case)

        response_data["failure_report"] = {
            "failure_id": report.failure_id,
            "category": report.category,
            "type": report.type,
            "severity": report.severity.value if hasattr(report.severity, "value") else str(report.severity),
            "reason": report.message,
            "confidence": report.confidence,
            "evidence": report.evidence,
        }

        response_data["regression_test"] = {
            "id": reg_test.id,
            "name": reg_test.name,
            "source_failure_id": reg_test.source_failure_id,
            "target_test_case": reg_test.test_case.name,
            "required_invariant": "check_order -> refund_order",
            "status": "Active (Enforced in CI/CD pipeline)",
            "created_at": reg_test.created_at.isoformat() if reg_test.created_at else None,
        }

    return response_data


# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "AI Reliability Studio API running. Open /static/index.html"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
