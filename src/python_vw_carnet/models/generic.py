from pydantic import BaseModel


class Data(BaseModel):
    correlationId: str


class GenericCorrelationIdResponse(BaseModel):
    data: Data
