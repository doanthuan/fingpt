from app.bb_retail.request import list_accounts, list_contacts
from app.core.config import settings
from app.core.context import RequestContext
from app.entity import (
    ApiHeader,
    FieldStatus,
    Intent,
    IntentMetadataForMoneyTransfer,
    IntentReqDto,
    IntentRespDto,
)
from app.entity.bb_api import BbApiConfig, BbQueryParams
from app.prompt.prompt_service import PromptService
from app.utils.modified_langfuse_decorator import observe  # type: ignore


class IntentService:
    def __init__(
        self,
        prompt_srv: PromptService,
    ) -> None:
        self._prompt_srv = prompt_srv
        self._chain = None

    async def load_prompt(  # type: ignore
        self,
        ctx: RequestContext,
        name: str,
        label: str,
    ):
        prompt = await self._prompt_srv.get_prompt(ctx, name, label, "chat")
        llm = prompt.llm_model.with_structured_output(IntentRespDto)  # type: ignore
        return prompt.tmpl | llm  # type: ignore

    @observe(name="analyze_intent")
    async def analyze_intent(
        self,
        ctx: RequestContext,
        header: ApiHeader,
        req: IntentReqDto,
    ) -> IntentRespDto:
        if not self._chain:  # type: ignore
            self._chain = await self.load_prompt(  # type: ignore
                ctx,
                settings.analyze_intent_prompt,
                settings.analyze_intent_label,
            )

        payload = req.metadata.model_dump_json() if req.metadata else "{}"
        resp = await self._chain.ainvoke(  # type: ignore
            input={
                "message_history": req.messages,
                "current_payload": payload,
            },
        )

        intent_payload = IntentRespDto.model_validate(resp)
        bb_config = BbApiConfig(
            ebp_access_token=header.token,
            ebp_cookie=header.cookie,
            ebp_edge_domain=settings.ebp_edge_domain,
        )

        if intent_payload.intent == Intent.MONEY_TRANSFER:
            metadata = IntentMetadataForMoneyTransfer.model_validate(
                intent_payload.metadata
            )
            recipient_data = metadata.recipient.value
            account_data = metadata.account.value

            if recipient_data and len(recipient_data) <= 2 and "name" in recipient_data:
                name = recipient_data["name"]
                contacts = await list_contacts(ctx, bb_config, BbQueryParams())
                filtered_contacts = [
                    contact
                    for contact in contacts
                    if name.lower() in contact.name.lower()
                ]
                if filtered_contacts:
                    metadata.recipient.status = FieldStatus.AVAILABLE
                    metadata.recipient.value = filtered_contacts[0].model_dump()
                else:
                    metadata.recipient.status = FieldStatus.NOT_FOUND
                    metadata.recipient.value = None

            if (account_data and len(account_data) <= 2) or (
                metadata.amount.value
                and metadata.currency.value
                and metadata.recipient.value
            ):
                accounts = await list_accounts(ctx, bb_config)
                account = max(accounts, key=lambda acc: acc.available_balance)
                metadata.account.status = FieldStatus.AVAILABLE
                metadata.account.value = account.dict()

        return intent_payload
