from pydantic import BaseModel
from enum import Enum
from typing import List
from uuid import UUID


class Status(Enum):
    AVAILABLE = "AVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class StatusEnum(Enum):
    OFF = "OFF"


class PlayProtection(BaseModel):
    status: StatusEnum


class Privilege(Enum):
    Delete = "Delete"
    Read = "Read"
    Write = "Write"


class Operation(BaseModel):
    longCode: str
    shortCode: str
    privilege: List[Privilege]
    capabilityStatus: Status
    subscriptionStatus: Status
    playProtection: PlayProtection


class Service(BaseModel):
    longCode: str
    shortCode: str
    operations: List[Operation]


class RolesAndRights(BaseModel):
    vehicleId: UUID
    userId: UUID
    startDate: int
    isInVehicle: bool
    isInGarage: bool
    privileges: List[str]
    roles: List[str]
    services: List[Service]
    tsp: str


class Data(BaseModel):
    rolesAndRights: RolesAndRights
    carnetVehicleToken: str


class VehicleSessionRequest(BaseModel):
    idToken: str
    tsp: str
    spinHash: str


class VehicleSessionResponse(BaseModel):
    data: Data
