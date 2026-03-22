from pydantic import BaseModel
from uuid import UUID


class Location(BaseModel):
    latitude: float
    longitude: float
    headingDirection: str


class Data(BaseModel):
    vehicleId: UUID
    eventTimeStamp: int
    location: Location
    source: str
    locationConfidence: int
    locationConfidenceInd: bool
    parked: bool
    vehicleStatusReason: int


class VehicleLocationResponse(BaseModel):
    data: Data
