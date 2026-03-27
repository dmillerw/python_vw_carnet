from typing import Literal

from pydantic import BaseModel


class AccessTokenExchangeRequest(BaseModel):
    code: str
    client_id: str
    redirect_uri: str
    code_verifier: str
    grant_type: Literal["authorization_code"]


class RefreshTokenRequest(BaseModel):
    refresh_token: str
    client_id: str
    grant_type: Literal["refresh_token"]
    code_verifier: str


class AccessTokenResponse(BaseModel):
    access_token: str
    expires_in: int
    id_token: str
    id_expires_in: int
    token_type: Literal["Bearer"]
    refresh_token: str
    refresh_expires_in: int
