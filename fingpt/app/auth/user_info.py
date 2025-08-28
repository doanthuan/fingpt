from pydantic import BaseModel

from app.auth.constant import EDGE_DOMAIN, IDENTITY_DOMAIN
from app.entity import AuthReqDto


class UserInfo(BaseModel):
    username: str
    password: str
    installation_name: str
    runtime_name: str
    identity_domain: str
    edge_domain: str

    @staticmethod
    def from_auth_req(
        req: AuthReqDto,
    ) -> "UserInfo":
        installation_name, runtime_name, _ = req.username.split("-")
        return UserInfo(
            username=req.username,
            password=req.password,
            installation_name=installation_name,
            runtime_name=runtime_name,
            identity_domain=IDENTITY_DOMAIN.format(
                runtime_name=runtime_name,
                installation_name=installation_name,
            ),
            edge_domain=EDGE_DOMAIN.format(
                user_type=req.user_type.value,
                runtime_name=runtime_name,
                installation_name=installation_name,
            ),
        )
