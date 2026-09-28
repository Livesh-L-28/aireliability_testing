"""Reliability Testing and Regression Generation Demo.

Demonstrates:
1. Deterministic evaluation of tool execution invariants (ToolOrder).
2. Failure analysis and structured failure reporting (FailureAnalyzer).
3. Automatic regression test generation from failures (RegressionGenerator).
"""

from aireliability import (
    ToolOrder,
    FailureAnalyzer,
    RegressionGenerator,
    TestCase,
)
from app import refund_agent, broken_refund_agent


def main():
    order_id = "ORD-1001"

    # Business Invariant: check_order must execute before refund_order
    invariant = ToolOrder(
        expected_order=["check_order", "refund_order"],
        name="check_before_refund_invariant",
    )

    test_case = TestCase(
        id="TC-REFUND-001",
        name="Refund Order Invariant Verification",
        input={"request": f"Refund order {order_id}"},
        expected_output=f"Order {order_id} refunded successfully",
    )

    print("=" * 50)
    print("RELIABILITY TEST SUITE")
    print("=" * 50)

    # ----------------------------------------------------
    # PHASE 2: Test Correct Agent
    # ----------------------------------------------------
    print("\nCorrect Agent")
    print("-------------")
    _, correct_trace = refund_agent(order_id)
    actual_order_correct = " -> ".join(s.name for s in correct_trace.steps)
    print(f"Workflow: {actual_order_correct}")

    eval_pass = invariant.evaluate(correct_trace, test_case)
    if eval_pass.passed:
        print("RELIABILITY TEST: check_order before refund_order: PASS")
    else:
        print(f"RELIABILITY TEST: check_order before refund_order: FAIL ({eval_pass.message})")

    # ----------------------------------------------------
    # PHASE 3: Test Broken Agent (Intentional Failure)
    # ----------------------------------------------------
    print("\nBroken Agent")
    print("------------")
    _, broken_trace = broken_refund_agent(order_id)
    actual_order_broken = " -> ".join(s.name for s in broken_trace.steps)
    print(f"Workflow: {actual_order_broken}")

    eval_fail = invariant.evaluate(broken_trace, test_case)
    if not eval_fail.passed:
        print("RELIABILITY TEST: check_order before refund_order: FAIL")
        print("FAILURE: refund_order was executed before check_order.")
    else:
        print("RELIABILITY TEST: PASS")

    # ----------------------------------------------------
    # PHASE 4: Structured Failure Report
    # ----------------------------------------------------
    print("\nFailure Report")
    print("--------------")
    analyzer = FailureAnalyzer()
    failure_report = analyzer.analyze(broken_trace, eval_fail, test_id=test_case.id)

    print(f"Failure ID: {failure_report.failure_id}")
    print(f"Category:   {failure_report.category.upper()}")
    print(f"Type:       {failure_report.type}")
    print(f"Severity:   {failure_report.severity.value.upper()}")
    print(f"Reason:     {failure_report.message.splitlines()[0]}")
    print(f"Evidence:   Expected {failure_report.evidence.get('expected_order')} but got {failure_report.evidence.get('actual_order')}")

    # ----------------------------------------------------
    # PHASE 5: Regression Test Generation
    # ----------------------------------------------------
    print("\nRegression Test Generated")
    print("-------------------------")
    generator = RegressionGenerator()
    regression_test = generator.generate(failure_report, test_case)

    print(f"Regression Test ID: {regression_test.id}")
    print(f"Source failure:     {regression_test.source_failure_id}")
    print("Required invariant:")
    print("    check_order -> refund_order")
    print(f"Target Test Case:   {regression_test.test_case.name}")
    print("Protection Status:  Active (Guards against tool inversion in future runs)")


if __name__ == "__main__":
    main()
