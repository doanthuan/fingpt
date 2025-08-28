from typing import Optional

from dotenv import load_dotenv
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

ENV_ERR_MSG = (
    "Error missing ENVIRONMENT variable. "
    "Please go to 1Password to get latest ENVIRONMENT variables "
    "and update your local .env file."
)


class Settings(BaseSettings):

    model_config = SettingsConfigDict()

    allowed_sec_api_calls: str = "false"
    root_path: str = ""
    port: str = "8000"
    assets_base_url: str = "http://localhost:8000"
    assets_url_prefix: str = "assets"

    langchain_tracing_v2: str = "true"
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_api_key: str = ""
    langchain_project: str = "fin-gpt"

    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = ""
    openai_api_version: str = ""
    openai_api_type: str = "azure"
    llm_temperature: float = 0.0

    azure_text_embedding_deployment: str = ""

    chroma_collection_name: str = ""
    chroma_persist_dir: str = ""
    chroma_search_distance: str = ""

    langfuse_secret_key: str = ""
    langfuse_public_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    enable_langfuse_tracer: bool = True

    ticker_report_analyze_income_stmt_prompt: str = ""
    ticker_report_analyze_income_stmt_label: str = ""
    ticker_report_analyze_balance_sheet_prompt: str = ""
    ticker_report_analyze_balance_sheet_label: str = ""
    ticker_report_analyze_cash_flow_prompt: str = ""
    ticker_report_analyze_cash_flow_label: str = ""
    ticker_report_summarize_report_prompt: str = ""
    ticker_report_summarize_report_label: str = ""
    ticker_report_symbol_detection_prompt: str = ""
    ticker_report_symbol_detection_label: str = ""
    ticker_report_symbol_identifier_agent_prompt: str = ""
    ticker_report_symbol_identifier_agent_label: str = ""

    self_check_user_query_prompt: str = ""
    self_check_user_query_label: str = ""
    self_check_bot_response_prompt: str = ""
    self_check_bot_response_label: str = ""

    transaction_report_state_agent_prompt: str = ""
    transaction_report_state_agent_label: str = ""
    transaction_report_search_term_prompt: str = ""
    transaction_report_search_term_label: str = ""
    transaction_report_agent_prompt: str = ""
    transaction_report_agent_label: str = ""

    transfer_extract_info_prompt_env: str = ""
    transfer_extract_info_label_env: str = ""
    money_transfer_agent_prompt: str = ""
    money_transfer_agent_label: str = ""
    transfer_v2_extract_info_prompt: str = ""
    transfer_v2_extract_info_prompt_label: str = ""

    term_deposit_controller_prompt: str = ""
    term_deposit_controller_label: str = ""
    new_term_deposit_extract_info_prompt_env: str = ""
    new_term_deposit_extract_info_label_env: str = ""
    term_deposit_extract_info_prompt_env: str = ""
    term_deposit_extract_info_label_env: str = ""
    term_deposit_v2_extract_info_prompt: str = ""
    term_deposit_v2_extract_info_label: str = ""

    renew_card_extract_user_query_intent_prompt_env: str = ""
    renew_card_extract_user_query_intent_label_env: str = ""
    card_controller_prompt: str = ""
    card_controller_label: str = ""
    card_v2_extract_user_query_prompt: str = ""
    card_v2_extract_user_query_label: str = ""

    assistant_primary_summarize_messages_prompt: str = ""
    assistant_primary_summarize_messages_label: str = ""

    image_save_mode: str = "local"
    image_save_path: str = ""

    ebp_edge_domain: str = ""
    ebp_test_account_username: str = ""
    ebp_test_account_password: str = ""

    assistant_state_path: str = ""

    assistant_primary_prompt: str = ""
    assistant_primary_label: str = ""
    new_term_deposit_extract_info_prompt_env: str = ""
    new_term_deposit_extract_info_label_env: str = ""

    app_version: str = "0.0.0"
    runtime: str = "local"

    sentry_dsn: Optional[str] = None
    sentry_traces_sample_rate: float = 0.0
    sentry_profiles_sample_rate: float = 0.0

    enable_semantic_cache: bool = False

    analyze_intent_prompt: str = ""
    analyze_intent_label: str = ""


try:
    settings = Settings()
except Exception:
    message = ENV_ERR_MSG
    logger.error(message)
    raise Exception(message)
