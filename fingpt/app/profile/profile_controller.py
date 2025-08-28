import traceback

from fastapi import HTTPException

from app.bb_retail.request import list_cards, list_term_deposit_accounts
from app.core.config import settings
from app.core.context import RequestContext
from app.entity.api import ApiHeader
from app.entity.bb_api import BbApiConfig
from app.entity.card import Card
from app.entity.offer import (
    OfferProduct,
    OfferReqDataForCard,
    OfferReqDataForTermDeposit,
    OfferResp,
    OfferRespDataForCard,
    OfferRespDataForTermDeposit,
    OfferType,
)
from app.entity.profile import ProfileDataReq, ProfileDataResp
from app.entity.term_deposit import TermDepositAccount
from app.utils.modified_langfuse_decorator import observe  # type: ignore
from app.utils.modified_langfuse_decorator import langfuse_context


class ProfileController:
    def __init__(
        self,
    ):
        self.profiles: dict[str, ProfileDataResp] = {}

    @observe(name="Update user profile")
    async def update_profile(
        self,
        ctx: RequestContext,
        header: ApiHeader,
        username: str,
        req: ProfileDataReq,
    ) -> ProfileDataResp:
        logger = ctx.logger()
        langfuse_context.update_current_trace(
            session_id=ctx.request_id(),
        )
        logger.info(f'Updating user profile with input: "{req}"')
        try:
            api_config = BbApiConfig(
                ebp_access_token=header.token,
                ebp_cookie=header.cookie,
                ebp_edge_domain=settings.ebp_edge_domain,
            )

            deposit_accounts: list[TermDepositAccount] = []
            cards: list[Card] = []
            renewals: list[OfferResp] = []
            if len(req.renewals) > 0:
                for offer in req.renewals:
                    if offer.product == OfferProduct.TERM_DEPOSIT:
                        if not deposit_accounts:
                            deposit_accounts = await list_term_deposit_accounts(
                                ctx, api_config
                            )
                        ids = [a.id for a in deposit_accounts]
                        data = OfferReqDataForTermDeposit.model_validate(offer.data)
                        if data.deposit_id not in ids:
                            raise HTTPException(
                                status_code=400,
                                detail="Invalid deposit_id",
                            )

                        renewals.append(
                            OfferResp(
                                product=OfferProduct.TERM_DEPOSIT,
                                message=offer.message,
                                data=OfferRespDataForTermDeposit(
                                    type=OfferType.RENEWAL,
                                    deposit_id=data.deposit_id,
                                ),
                            )
                        )

                    elif offer.product == OfferProduct.CARD:
                        if not cards:
                            cards = await list_cards(ctx, api_config)
                        data = OfferReqDataForCard.model_validate(offer.data)
                        filtered = list(filter(lambda c: c.id == data.card_id, cards))  # type: ignore
                        if not filtered:
                            raise HTTPException(
                                status_code=400,
                                detail="Invalid card_id",
                            )

                        renewals.append(
                            OfferResp(
                                product=OfferProduct.CARD,
                                message=offer.message,
                                data=OfferRespDataForCard(
                                    type=OfferType.RENEWAL,
                                    card=None,  # TODO: Fix the conflict between Pydantic V1 vs V2
                                ),
                            )
                        )

                    else:
                        logger.error(f"Invalid product: {offer.product}")
                        raise HTTPException(
                            status_code=400,
                            detail="Invalid product",
                        )

                self.profiles[username] = ProfileDataResp(renewals=renewals)
            return self.profiles[username]

        except HTTPException as e:
            raise e

        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail="Internal server error: " + str(e),
            )
        finally:
            logger.info("Controller exiting...")

    @observe(name="Get user profile")
    async def get_profile(self, ctx: RequestContext, username: str) -> ProfileDataResp:
        logger = ctx.logger()
        langfuse_context.update_current_trace(
            session_id=ctx.request_id(),
        )
        logger.info(f'Getting user profile with username: "{username}"')
        try:
            return self.profiles.get(username, None) or ProfileDataResp(renewals=[])

        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail="Internal server error: " + str(e),
            )
        finally:
            logger.info("Controller exiting...")
