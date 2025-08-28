import asyncio
from typing import Any

from deepeval.metrics import BaseMetric  # type: ignore
from deepeval.test_case import LLMTestCase  # type: ignore
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import AzureChatOpenAI

from app.core.config import settings
from app.core.context import RequestContext
from app.entity import ChatPrompt
from app.utils.modified_langfuse_decorator import langfuse_context  # type: ignore
from app.utils.modified_langfuse_decorator import observe


class LlmService:
    """
    A service class to interact with the Azure OpenAI model using LangChain.
    """

    def __init__(
        self,
    ):
        """
        Initializes the LlmService with an Azure OpenAI model.
        """
        self._model = AzureChatOpenAI(
            azure_deployment=settings.azure_openai_deployment,
        )

    @observe()
    async def invoke(
        self,
        *,
        ctx: RequestContext,
        prompt: ChatPrompt,
        metrics: list[BaseMetric] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Invokes the Azure OpenAI model with the given prompt and context.

        Args:
            ctx (RequestContext): The request context containing logger and other metadata.
            prompt (ChatPrompt): The chat prompt to be sent to the model.
            metrics (list[BaseMetric], optional): A list of metrics to be used for evaluation. Defaults to None.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            str: The response from the model.
        """
        logger = ctx.logger()
        chain = prompt.tmpl | self._model | StrOutputParser()  # type: ignore
        logger.debug(f"Awaiting reply for prompt {prompt.name}...")

        try:
            langfuse_handler = langfuse_context.get_current_langchain_handler()
            callbacks = [langfuse_handler]
        except Exception as e:
            logger.error(f"Error getting langfuse handler: {str(e)}")
            callbacks = []

        output = await chain.ainvoke(  # type: ignore
            input=kwargs,
            config={"callbacks": callbacks},  # type: ignore
        )

        asyncio.create_task(
            self._evaluate(
                ctx,
                prompt=prompt,
                input=await prompt.tmpl.aformat(**kwargs),
                output=output,
                retrieval_context=list(kwargs.values()),
                metrics=metrics,
            )
        )

        logger.info(f"Returning output for {prompt.name}...")
        return output

    @observe()
    async def _evaluate(
        self,
        *,
        ctx: RequestContext,
        prompt: ChatPrompt,
        input: str,
        output: str,
        context: list[Any] | None = None,
        retrieval_context: list[Any] | None = None,
        metrics: list[BaseMetric] | None = None,
    ):
        logger = ctx.logger()
        if not metrics:
            logger.info("No metrics to evaluate...")
            return

        if metrics:
            logger.warn("Put your evalution code in ./experiments instead of here")
            return

        logger.debug(f"Evaluating {prompt.name} output...")
        test_case = LLMTestCase(
            input=input,
            actual_output=output,
            context=[str(c) for c in context] if context else None,
            retrieval_context=(
                [str(c) for c in retrieval_context] if retrieval_context else None
            ),
        )

        logger.info(f"Running {len(metrics)} metrics for {prompt.name}...")
        for metric in metrics:
            await metric.a_measure(test_case)  # type: ignore

        logger.info(f"Shipping {len(metrics)} metrics for {prompt.name}...")
        for metric in metrics:
            langfuse_context.score_current_observation(
                name=str(metric.__class__.__name__),
                value=str(metric.score),
                comment=metric.reason,
            )

        logger.info(f"Done evaluation for {prompt.name}")
