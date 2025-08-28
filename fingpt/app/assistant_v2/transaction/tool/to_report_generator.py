from langchain_core.pydantic_v1 import BaseModel


class ToReportGenerator(BaseModel):
    """
    What this function do: Transfers work to a specialized transaction assistant to handle report generation.
    When to call: When user asks for a report of their historical transactions or their transaction activity report.
    Example: User: Show me my transactions for the last month.
    This tool will be used to generate the report of the transactions for the last month.
    """

    pass
