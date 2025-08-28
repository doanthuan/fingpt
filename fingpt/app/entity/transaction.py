from pydantic import BaseModel


class Transaction(BaseModel):
    account_id: str
    execution_date: str
    transaction_type: str
    amount: float
    currency: str
    counterparty_name: str
    counterparty_account: str
