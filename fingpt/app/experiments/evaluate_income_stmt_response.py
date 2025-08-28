import langfuse
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase

INCOME_STMT_DATASET_NAME = "income_statement_analysis_evaluation"
BALANCE_SHEET_DATASET_NAME = "income_statement_analysis_evaluation"


async def test_income_stmt():
    metrics = [
        AnswerRelevancyMetric(threshold=0.7),
        FaithfulnessMetric(),
    ]
    answer_relevancy_metric = AnswerRelevancyMetric(threshold=0.7)
    datasets = [
        INCOME_STMT_DATASET_NAME,
        BALANCE_SHEET_DATASET_NAME,
    ]
    for dataset in datasets:
        dataset = langfuse.get_dataset(dataset)
        for item in dataset.items:  # type: ignore
            assert_test(item, [metrics])
            test_case = LLMTestCase(
                input="What if these shoes don't fit?",
                actual_output="We offer a 30-day full refund at no extra cost.",
            )
            assert_test(test_case, [answer_relevancy_metric])
