"""Customer Support Refund Agent Demo.

Demonstrates how agent actions are executed and captured as an
aireliability ExecutionTrace.
"""

from datetime import datetime, timezone
import uuid
from aireliability import ExecutionTrace, TraceStep, StepType


def check_order(order_id: str) -> dict:
    """Check if the order is eligible for refund."""
    return {"order_id": order_id, "eligible": True}


def refund_order(order_id: str) -> dict:
    """Process the refund for the order."""
    return {"order_id": order_id, "status": "refunded"}


def refund_agent(order_id: str) -> tuple[str, ExecutionTrace]:
    """Correct Agent: verifies order eligibility before issuing a refund.

    Business Rule Invariant: check_order -> refund_order
    """
    t_start = datetime.now(timezone.utc)
    steps: list[TraceStep] = []

    # Step 1: Tool call - check_order
    chk_res = check_order(order_id)
    steps.append(
        TraceStep(
            type=StepType.TOOL,
            name="check_order",
            input={"order_id": order_id},
            output=chk_res,
        )
    )

    # Step 2: Tool call - refund_order
    ref_res = refund_order(order_id)
    steps.append(
        TraceStep(
            type=StepType.TOOL,
            name="refund_order",
            input={"order_id": order_id},
            output=ref_res,
        )
    )

    t_end = datetime.now(timezone.utc)
    final_output = f"Order {order_id} refunded successfully"

    # Capture execution as an aireliability ExecutionTrace
    trace = ExecutionTrace(
        trace_id=f"trace_{uuid.uuid4().hex[:12]}",
        test_id="refund_order_flow",
        started_at=t_start,
        completed_at=t_end,
        input={"request": f"Refund order {order_id}"},
        output=final_output,
        steps=steps,
    )

    return final_output, trace


def broken_refund_agent(order_id: str) -> tuple[str, ExecutionTrace]:
    """Broken Agent: intentionally executes refund_order before check_order.

    Violates Business Rule Invariant: check_order -> refund_order
    """
    t_start = datetime.now(timezone.utc)
    steps: list[TraceStep] = []

    # Step 1: Tool call - refund_order (BUG: refunding prior to verification)
    ref_res = refund_order(order_id)
    steps.append(
        TraceStep(
            type=StepType.TOOL,
            name="refund_order",
            input={"order_id": order_id},
            output=ref_res,
        )
    )

    # Step 2: Tool call - check_order
    chk_res = check_order(order_id)
    steps.append(
        TraceStep(
            type=StepType.TOOL,
            name="check_order",
            input={"order_id": order_id},
            output=chk_res,
        )
    )

    t_end = datetime.now(timezone.utc)
    final_output = f"Order {order_id} refunded successfully"

    trace = ExecutionTrace(
        trace_id=f"trace_{uuid.uuid4().hex[:12]}",
        test_id="refund_order_flow",
        started_at=t_start,
        completed_at=t_end,
        input={"request": f"Refund order {order_id}"},
        output=final_output,
        steps=steps,
    )

    return final_output, trace


if __name__ == "__main__":
    order_id = "ORD-1001"
    print(f"Agent request: Refund order {order_id}")

    output, trace = refund_agent(order_id)
    for step in trace.steps:
        print(f"Tool: {step.name}")
    print(f"Result: {output}")
