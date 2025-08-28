from pydantic import BaseModel

from app.entity.offer import OfferReq, OfferResp


class ProfileDataReq(BaseModel):
    renewals: list[OfferReq] = []


class ProfileDataResp(BaseModel):
    renewals: list[OfferResp] = []
