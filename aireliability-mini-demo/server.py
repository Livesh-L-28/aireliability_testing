"""FastAPI Web Server for AI Reliability Testing Demo.

Exposes REST APIs to run:
- Correct Agent vs Broken Agent workflows
- Deterministic Invariant checks (ToolOrder)
- Structured Failure Analysis (FailureAnalyzer)
- Automated Regression Test Generation (RegressionGenerator)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

from aireliability import (
    ToolOrder,
    FailureAnalyzer,
    RegressionGenerator,
    TestCase,
)
from app import refund_agent, broken_refund_agent

app = FastAPI(title="AI Reliability Testing Studio", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema
class RunAgentRequest(BaseModel):
    order_id: str = "ORD-1001"
    agent_type: str = "correct"  # "correct" or "broken"


@app.post("/api/run-agent")
def run_agent_api(req: RunAgentRequest):
    order_id = req.order_id.strip() or "ORD-1001"
    
    if req.agent_type == "broken":
        output, trace = broken_refund_agent(order_id)
        mode = "Broken Agent (Tools Inverted)"
    else:
        output, trace = refund_agent(order_id)
        mode = "Correct Agent (Compliant)"

    # Format steps for the UI
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
    
    # 1. Run agent
    if req.agent_type == "broken":
        agent_name = "Broken Agent (Tool Inversion)"
        output, trace = broken_refund_agent(order_id)
    else:
        agent_name = "Correct Agent (Compliant Order)"
        output, trace = refund_agent(order_id)

    # 2. Define invariant
    invariant = ToolOrder(
        expected_order=["check_order", "refund_order"],
        name="check_before_refund_invariant",
    )

    test_case = TestCase(
        id=f"TC-REFUND-{order_id}",
        name="Refund Order Invariant Verification",
        input={"request": f"Refund order {order_id}"},
        expected_output=f"Order {order_id} refunded successfully",
    )

    # 3. Evaluate trace against invariant
    eval_result = invariant.evaluate(trace, test_case)

    # Steps for trajectory visualizer
    steps_data = []
    for idx, s in enumerate(trace.steps, start=1):
        steps_data.append({
            "step_num": idx,
            "type": s.type.value if hasattr(s.type, "value") else str(s.type),
            "name": s.name,
            "input": s.input,
            "output": s.output,
        })

    response_data = {
        "agent_name": agent_name,
        "agent_type": req.agent_type,
        "order_id": order_id,
        "agent_output": output,
        "trace_id": trace.trace_id,
        "steps": steps_data,
        "evaluation": {
            "passed": eval_result.passed,
            "score": eval_result.score,
            "evaluator": eval_result.evaluator,
            "message": eval_result.message,
            "expected_order": ["check_order", "refund_order"],
            "actual_order": [s.name for s in trace.steps],
        },
        "failure_report": None,
        "regression_test": None,
    }

    # 4. If failed, analyze failure & generate regression test
    if not eval_result.passed:
        analyzer = FailureAnalyzer()
        report = analyzer.analyze(trace, eval_result, test_id=test_case.id)

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
