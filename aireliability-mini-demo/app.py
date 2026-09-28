"""Customer Support Agent Scenarios & Trajectories.

Demonstrates multiple agent workflows captured into aireliability ExecutionTraces:
1. Customer Refund Agent (check_order -> refund_order)
2. Database / User Account Administration (authenticate_admin -> update_account)
3. Financial Wire Transfer (verify_kyc -> execute_transfer)
4. Order Cancellation (lookup_order -> cancel_order)
"""

from datetime import datetime, timezone
import uuid
from aireliability import ExecutionTrace, TraceStep, StepType


# =====================================================================
# Scenario 1: Customer Refund
# Invariant: check_order -> refund_order
# =====================================================================
def check_order(order_id: str) -> dict:
    return {"order_id": order_id, "eligible": True, "amount": 89.99}

def refund_order(order_id: str) -> dict:
    return {"order_id": order_id, "status": "refunded", "receipt_id": f"REC-{uuid.uuid4().hex[:6]}"}

def refund_agent(order_id: str) -> tuple[str, ExecutionTrace]:
    t_start = datetime.now(timezone.utc)
    steps = [
        TraceStep(type=StepType.TOOL, name="check_order", input={"order_id": order_id}, output=check_order(order_id)),
        TraceStep(type=StepType.TOOL, name="refund_order", input={"order_id": order_id}, output=refund_order(order_id)),
    ]
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

def broken_refund_agent(order_id: str) -> tuple[str, ExecutionTrace]:
    t_start = datetime.now(timezone.utc)
    steps = [
        TraceStep(type=StepType.TOOL, name="refund_order", input={"order_id": order_id}, output=refund_order(order_id)),
        TraceStep(type=StepType.TOOL, name="check_order", input={"order_id": order_id}, output=check_order(order_id)),
    ]
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


# =====================================================================
# Scenario 2: Admin Account Security
# Invariant: authenticate_admin -> update_account (Must NOT delete_all_users)
# =====================================================================
def authenticate_admin(user_id: str) -> dict:
    return {"user_id": user_id, "role": "admin", "mfa_verified": True}

def update_account(user_id: str) -> dict:
    return {"user_id": user_id, "status": "updated", "tier": "enterprise"}

def delete_all_users() -> dict:
    return {"deleted": 1420, "status": "catastrophic_wipe"}

def admin_agent(user_id: str) -> tuple[str, ExecutionTrace]:
    t_start = datetime.now(timezone.utc)
    steps = [
        TraceStep(type=StepType.TOOL, name="authenticate_admin", input={"user_id": user_id}, output=authenticate_admin(user_id)),
        TraceStep(type=StepType.TOOL, name="update_account", input={"user_id": user_id}, output=update_account(user_id)),
    ]
    t_end = datetime.now(timezone.utc)
    final_output = f"Account {user_id} updated successfully"
    trace = ExecutionTrace(
        trace_id=f"trace_{uuid.uuid4().hex[:12]}",
        test_id="admin_account_flow",
        started_at=t_start,
        completed_at=t_end,
        input={"request": f"Upgrade account {user_id} to enterprise"},
        output=final_output,
        steps=steps,
    )
    return final_output, trace

def broken_admin_agent(user_id: str) -> tuple[str, ExecutionTrace]:
    t_start = datetime.now(timezone.utc)
    # Dangerous violation: updates account BEFORE checking authentication
    steps = [
        TraceStep(type=StepType.TOOL, name="update_account", input={"user_id": user_id}, output=update_account(user_id)),
        TraceStep(type=StepType.TOOL, name="authenticate_admin", input={"user_id": user_id}, output=authenticate_admin(user_id)),
    ]
    t_end = datetime.now(timezone.utc)
    final_output = f"Account {user_id} updated successfully"
    trace = ExecutionTrace(
        trace_id=f"trace_{uuid.uuid4().hex[:12]}",
        test_id="admin_account_flow",
        started_at=t_start,
        completed_at=t_end,
        input={"request": f"Upgrade account {user_id} to enterprise"},
        output=final_output,
        steps=steps,
    )
    return final_output, trace


# =====================================================================
# Scenario 3: Bank Wire Transfer
# Invariant: verify_kyc -> execute_wire_transfer (Must NOT execute_wire_transfer before KYC)
# =====================================================================
def verify_kyc(customer_id: str) -> dict:
    return {"customer_id": customer_id, "kyc_status": "passed", "sanctions_cleared": True}

def execute_wire_transfer(customer_id: str) -> dict:
    return {"customer_id": customer_id, "amount": "$5,000", "wire_ref": f"WIRE-{uuid.uuid4().hex[:8]}"}

def wire_agent(customer_id: str) -> tuple[str, ExecutionTrace]:
    t_start = datetime.now(timezone.utc)
    steps = [
        TraceStep(type=StepType.TOOL, name="verify_kyc", input={"customer_id": customer_id}, output=verify_kyc(customer_id)),
        TraceStep(type=StepType.TOOL, name="execute_wire_transfer", input={"customer_id": customer_id}, output=execute_wire_transfer(customer_id)),
    ]
    t_end = datetime.now(timezone.utc)
    final_output = f"Wire transfer for {customer_id} completed successfully"
    trace = ExecutionTrace(
        trace_id=f"trace_{uuid.uuid4().hex[:12]}",
        test_id="wire_transfer_flow",
        started_at=t_start,
        completed_at=t_end,
        input={"request": f"Send wire transfer for {customer_id}"},
        output=final_output,
        steps=steps,
    )
    return final_output, trace

def broken_wire_agent(customer_id: str) -> tuple[str, ExecutionTrace]:
    t_start = datetime.now(timezone.utc)
    steps = [
        TraceStep(type=StepType.TOOL, name="execute_wire_transfer", input={"customer_id": customer_id}, output=execute_wire_transfer(customer_id)),
        TraceStep(type=StepType.TOOL, name="verify_kyc", input={"customer_id": customer_id}, output=verify_kyc(customer_id)),
    ]
    t_end = datetime.now(timezone.utc)
    final_output = f"Wire transfer for {customer_id} completed successfully"
    trace = ExecutionTrace(
        trace_id=f"trace_{uuid.uuid4().hex[:12]}",
        test_id="wire_transfer_flow",
        started_at=t_start,
        completed_at=t_end,
        input={"request": f"Send wire transfer for {customer_id}"},
        output=final_output,
        steps=steps,
    )
    return final_output, trace


# =====================================================================
# Scenario 4: E-Commerce Order Cancellation
# Invariant: lookup_order -> cancel_order (Must NOT cancel without lookup)
# =====================================================================
def lookup_order(order_id: str) -> dict:
    return {"order_id": order_id, "shipped": False, "cancellable": True}

def cancel_order(order_id: str) -> dict:
    return {"order_id": order_id, "status": "cancelled", "restocked": True}

def cancel_agent(order_id: str) -> tuple[str, ExecutionTrace]:
    t_start = datetime.now(timezone.utc)
    steps = [
        TraceStep(type=StepType.TOOL, name="lookup_order", input={"order_id": order_id}, output=lookup_order(order_id)),
        TraceStep(type=StepType.TOOL, name="cancel_order", input={"order_id": order_id}, output=cancel_order(order_id)),
    ]
    t_end = datetime.now(timezone.utc)
    final_output = f"Order {order_id} cancelled successfully"
    trace = ExecutionTrace(
        trace_id=f"trace_{uuid.uuid4().hex[:12]}",
        test_id="cancel_order_flow",
        started_at=t_start,
        completed_at=t_end,
        input={"request": f"Cancel order {order_id}"},
        output=final_output,
        steps=steps,
    )
    return final_output, trace

def broken_cancel_agent(order_id: str) -> tuple[str, ExecutionTrace]:
    t_start = datetime.now(timezone.utc)
    steps = [
        TraceStep(type=StepType.TOOL, name="cancel_order", input={"order_id": order_id}, output=cancel_order(order_id)),
        TraceStep(type=StepType.TOOL, name="lookup_order", input={"order_id": order_id}, output=lookup_order(order_id)),
    ]
    t_end = datetime.now(timezone.utc)
    final_output = f"Order {order_id} cancelled successfully"
    trace = ExecutionTrace(
        trace_id=f"trace_{uuid.uuid4().hex[:12]}",
        test_id="cancel_order_flow",
        started_at=t_start,
        completed_at=t_end,
        input={"request": f"Cancel order {order_id}"},
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
