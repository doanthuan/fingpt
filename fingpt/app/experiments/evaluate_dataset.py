import asyncio

from pydantic import BaseModel

# import langfuse
from app.entity.api import SupportedTicker

DATASET_NAME = "yfinance_llama3.1_testing"


class DatasetInput(BaseModel):
    ticker: SupportedTicker
    income_stmt_analysis: str
    balance_sheet_analysis: str
    cash_flow_analysis: str


# dataset = langfuse.get_dataset(DATASET_NAME)
# for item in dataset.items:


async def run_experiment():
    pass


if __name__ == "__main__":
    asyncio.run(run_experiment())
