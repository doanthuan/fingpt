import asyncio
import os
import subprocess
import uuid
from datetime import datetime
from typing import Any, Dict, Tuple

from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig
from langchain_openai import AzureChatOpenAI
from langfuse import Langfuse

from app.assistant.ticker.nodes import (
    balance_sheet_analyst,
    cash_flow_analyst,
    income_stmt_analyst,
    summary_analyst,
)
from app.assistant.ticker.state import TickerAgentState
from app.core.context import RequestContext
from app.prompt.prompt_service import PromptService
from app.utils.modified_langfuse_decorator import langfuse_context, observe

load_dotenv()

langfuse = Langfuse()
prompt_service = PromptService()

DATASET_NAMES = [
    "income_statement_analysis_evaluation",
    "balance_sheet_analysis_evaluation",
    "cash_flow_analysis_evaluation",
    "financial_summarization_evaluation",
]


def setup_environment() -> Tuple[str, RequestContext, AzureChatOpenAI, RunnableConfig]:
    x_request_id = str(uuid.uuid4())
    print(f"Request ID: {x_request_id}")
    request_context = RequestContext(x_request_id)

    llm_model = AzureChatOpenAI(azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"))

    config = RunnableConfig(
        configurable={
            "_ctx": request_context,
            "_ps": prompt_service,
            "_llm_model": llm_model,
        }
    )

    return x_request_id, request_context, llm_model, config


def get_git_commit_sha() -> str:
    try:
        sha = (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .decode("utf-8")
            .strip()
        )
        return sha[:7]
    except subprocess.CalledProcessError:
        return "unknown"


def get_current_timestamp() -> str:
    return datetime.now().isoformat()


def get_key_function_prompt_name(experiment_name: str) -> Tuple[Any, callable, str]:
    if "income" in experiment_name:
        return "income_stmt", income_stmt_analyst, "TICKER_REPORT_ANALYZE_INCOME_STMT"
    elif "balance" in experiment_name:
        return (
            "balance_sheet",
            balance_sheet_analyst,
            "TICKER_REPORT_ANALYZE_BALANCE_SHEET",
        )
    elif "cash" in experiment_name:
        return "cash_flow", cash_flow_analyst, "TICKER_REPORT_ANALYZE_CASH_FLOW"
    elif "summarization" in experiment_name:
        return (
            ["income_stmt", "balance_sheet", "cash_flow"],
            summary_analyst,
            "TICKER_REPORT_SUMMARIZE_REPORT",
        )
    raise ValueError(f"Unknown experiment name: {experiment_name}")


@observe()
async def run_experiment(
    experiment_name: str, input: Dict[str, Any]
) -> Tuple[Dict[str, Any], Any, Any, str]:
    key, function_to_use, langfuse_prompt_name = get_key_function_prompt_name(
        experiment_name
    )
    print(key)
    print(function_to_use)
    print(langfuse_prompt_name)

    if isinstance(key, str):  # Single key experiments
        state = TickerAgentState(
            {
                "company_info": {"industry": input["industry"]},
                key: input[key],
                "section_7": input["section_text"],
            }
        )
        report = await function_to_use(state=state, config=config)
        report = report[f"{key}_report"]
        report_data = {
            "industry": input["industry"],
            key: input[key],
            "section_text": input["section_text"],
            f"{key}_report": report,
        }
        print(report_data.keys())
    else:  # Summarization experiment
        state = TickerAgentState({f"{k}_report": input[f"{k}_analysis"] for k in key})
        report = await function_to_use(state=state, config=config)
        report = report["summary_report"]
        report_data = {f"{k}_report": input[f"{k}_analysis"] for k in key}
        report_data["summary_report"] = report
        print(report_data.keys())

    generation_start_time = datetime.now()
    langfuse_generation = langfuse.generation(
        session_id=x_request_id,
        name=experiment_name,
        input=input,
        output=report,
        model="gpt-4-32k-jul-18",
        start_time=generation_start_time,
        end_time=datetime.now(),
    )

    return report_data, langfuse_generation, key, langfuse_prompt_name


@observe()
async def run_evaluate(dataset_name: str):
    sha = get_git_commit_sha()
    timestamp = get_current_timestamp()
    experiment_name = f"{dataset_name}_{sha}_{timestamp}"

    dataset = langfuse.get_dataset(dataset_name)

    metrics = [
        AnswerRelevancyMetric(),
        FaithfulnessMetric(),
        GEval(
            name="Correctness GEval",
            evaluation_params=[
                LLMTestCaseParams.EXPECTED_OUTPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
            ],
            evaluation_steps=[
                "Compare the actual output with the expected output to assess overall quality.",
                (
                    "Evaluate if the actual output provides more detail or additional relevant information "
                    "not present in the expected output."
                ),
                (
                    "Check if the actual output demonstrates greater fluency, including better sentence structure, "
                    "flow, and readability."
                ),
                "Assess the clarity and coherence of the actual output compared to the expected output.",
                "Determine if the actual output offers deeper insights or a more thorough explanation of the topic.",
                "Identify any areas where the actual output improves upon or enhances the expected output.",
            ],
        ),
    ]

    for item in dataset.items[:1]:  # Limit to 1 item for testing
        report_data, langfuse_generation, key, langfuse_prompt_name = (
            await run_experiment(experiment_name, item.input)
        )
        item.link(langfuse_generation, experiment_name)

        prompt = await prompt_service.get_prompt(
            ctx=request_context,
            name=str(os.getenv(f"{langfuse_prompt_name}_PROMPT")),
            type="chat",
            label=str(os.getenv(f"{langfuse_prompt_name}_LABEL")),
        )

        if isinstance(key, str):
            input_data = {
                "industry": report_data["industry"],
                key: report_data[key],
                "section_text": report_data["section_text"],
            }
            retrieval_context = [report_data[key], report_data["section_text"]]
            actual_output = report_data[f"{key}_report"]
        else:
            input_data = {f"{k}_report": report_data[f"{k}_report"] for k in key}
            retrieval_context = [report_data[f"{k}_report"] for k in key]
            actual_output = report_data["summary_report"]

        input = await prompt.tmpl.aformat(**input_data)
        expected_output = item.expected_output

        test_case = LLMTestCase(
            input=input,
            actual_output=actual_output,
            retrieval_context=retrieval_context,
            expected_output=expected_output,
        )

        for metric in metrics:
            await metric.a_measure(test_case)
            langfuse_generation.score(
                name=metric.__class__.__name__,
                value=metric.score,
                comment=metric.reason,
            )


@observe()
async def run_experiment_unittest():
    langfuse_context.update_current_trace(session_id=x_request_id)
    await run_evaluate(dataset_name=DATASET_NAMES[2])


if __name__ == "__main__":
    x_request_id, request_context, llm_model, config = setup_environment()

    asyncio.run(run_experiment_unittest())
