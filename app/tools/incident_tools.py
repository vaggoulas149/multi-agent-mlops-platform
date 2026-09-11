"""Deterministic tools used by the incident investigation agents.

These tools intentionally return controlled demo data so the project can
focus on multi-agent orchestration rather than external data infrastructure.
"""

from langchain_core.tools import tool


@tool
def get_checkout_metrics(date: str) -> str:
    """Return checkout metrics for a specific date.

    Use this tool when investigating checkout performance, checkout
    conversion, or payment-related errors for a particular date.

    Args:
        date: Date for which checkout metrics should be retrieved.

    Returns:
        A compact string containing checkout conversion, payment error rate,
        and previous-day conversion evidence.
    """
    return (
        f"Metrics for {date}: "
        "conversion_rate=2.1%, "
        "payment_error_rate=8.4%, "
        "previous_day_conversion_rate=3.0%"
    )


@tool
def search_incidents(query: str) -> str:
    """Search historical operational incidents relevant to a query.

    Use this tool to retrieve evidence about previous outages, deployments,
    payment failures, checkout incidents, or similar production problems.

    Args:
        query: Natural-language description of the incident information to
            search for.

    Returns:
        A compact string containing relevant historical incident evidence.
    """
    return (
        "Incident INC-991: payment service deployment v2.4.1 "
        "caused elevated payment failures and reduced checkout conversion."
    )
