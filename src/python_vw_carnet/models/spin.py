from pydantic import BaseModel


class Data(BaseModel):
    challenge: str
    remainingTries: int


class SpinChallengeResponse(BaseModel):
    data: Data
