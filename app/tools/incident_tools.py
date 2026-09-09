from langchain_core.tools import tool


@tool
def get_checkout_metrics(date: str) -> str:
    """
    Return checkout metrics for a specific date.

    Use this tool when investigating checkout performance,
    checkout conversion, or payment errors for a given date.
    """
    return (
        f"Metrics for {date}: "
        "conversion_rate=2.1%, "
        "payment_error_rate=8.4%, "
        "previous_day_conversion_rate=3.0%"
    )


@tool
def search_incidents(query: str) -> str:
    """
    Search previous operational incidents.

    Use this tool to find previous outages, deployments,
    payment failures, checkout incidents, or similar
    production problems.
    """
    return (
        "Incident INC-991: payment service deployment v2.4.1 "
        "caused elevated payment failures and reduced checkout conversion."
    )
