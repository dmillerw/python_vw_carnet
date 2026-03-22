from pydantic import BaseModel


class DoorLockStatus(BaseModel):
    frontLeft: str
    frontRight: str
    rearLeft: str
    rearRight: str
    doorLockStatusTimestamp: int


class DoorStatus(BaseModel):
    frontLeft: str
    frontRight: str
    rearLeft: str
    rearRight: str
    trunk: str
    hood: str
    leftCargo: str
    rightCargo: str
    doorStatusTimestamp: int


class LightStatus(BaseModel):
    left: str
    right: str
    parking: str
    tail: str
    fog: str


class WindowStatus(BaseModel):
    frontLeft: str
    frontRight: str
    rearLeft: str
    rearRight: str
    convertibleTop: str
    sunRoof: str
    rearSunRoof: str
    windowStatusTimestamp: int


class ExteriorStatus(BaseModel):
    secure: str
    doorStatus: DoorStatus
    doorLockStatus: DoorLockStatus
    windowStatus: WindowStatus
    lightStatus: LightStatus


class LastParkedLocation(BaseModel):
    latitude: float
    longitude: float
    timestamp: int


class NextMaintenanceMilestone(BaseModel):
    mileageInterval: int
    absoluteMileage: int


class PowerStatus(BaseModel):
    cruiseRange: int
    fuelPercentRemaining: int
    cruiseRangeUnits: str
    cruiseRangeFirst: int


class Data(BaseModel):
    currentMileage: int
    nextMaintenanceMilestone: NextMaintenanceMilestone
    timestamp: int
    exteriorStatus: ExteriorStatus
    powerStatus: PowerStatus
    lastParkedLocation: LastParkedLocation
    clampState: str
    platform: str
    lockStatus: str
    clampStateTimestamp: int


class VehicleResponse(BaseModel):
    data: Data
