from langchain.tools import tool


@tool
def get_checkout_metrics(date: str) -> str:
    """
    Return checkout metrics for a specific date.
    Use this tool when investigating checkout performance.
    """
    return (
        f"Metrics for {date}: "
        "conversion_rate=2.1%, "
        "payment_error_rate=8.4%, "
        "previous_day_conversion_rate=3.0%"
    )